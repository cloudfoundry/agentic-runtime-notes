---
title: "Domyn Swarm — HPC-Native Batch Inference Orchestration for vLLM"
author: Ruben Koster (@rkoster)
date: 2026-08-19
tags: [runtime-lifecycle, orchestration, observability-governance]
status: draft
sources:
  - https://github.com/igeniusai/domyn-swarm
ratings:
  platform-impact:
    value: 75
    note: 'CF has Diego/CAPI workload lifecycle primitives, but no integrated equivalent for provisioning GPU inference endpoints across heterogeneous schedulers, supervising vLLM replicas, and reconciling durable batch-job state with resumable checkpoints.'
  maturity:
    value: 50
    note: 'Version 0.29.0 has a substantial implementation with migrations, health supervision, retries, checkpointing, and rapid releases through 2026, but it is classified Alpha, is not on PyPI, has 23 stars and one fork, and shows only internal Domyn dogfooding rather than broad production evidence.'
  novelty:
    value: 40
    note: 'The ServingBackend/ComputeBackend split applies familiar adapter and deployment-lifecycle patterns to HPC inference; watchdog supervision, SQLite reconciliation, and sharded Parquet checkpoints are a useful combination, but each is established technology rather than a new architecture.'
  actionability:
    value: 80
    note: 'The two small backend protocols define a bounded CF spike: implement serving and compute adapters for CAPI/Diego plus a GPU scheduler, then exercise endpoint lifecycle, job-status reconciliation, watchdog failure recovery, and Parquet resume behavior.'

---

## Summary

Domyn Swarm (`igeniusai/domyn-swarm`, Apache-2.0) is a CLI + Python library that stands up
vLLM OpenAI-compatible serving endpoints on **Slurm** or **DGX Cloud Lepton**, then runs
high-throughput batch inference jobs (DataFrame-in/DataFrame-out, or arbitrary scripts)
against them with retries, checkpointing, and process-level health supervision. This
analysis is based on a local checkout (commit `4824560`, tagged `v0.29.0-11-g4824560`,
2026-07-17) rather than the truncated GitHub web view — the codebase is considerably more
sophisticated than the public README alone suggests: it includes a SQLite-backed state/job
store with Alembic migrations, a dedicated watchdog/collector process pair for per-replica
health monitoring and auto-restart, and pluggable Parquet checkpoint stores with resumable,
shard-based writes. It is HPC batch-inference tooling, not a general agent framework — no
tool-calling, planning, or multi-agent orchestration concepts appear anywhere in the codebase.

## Key findings

**Core abstraction: two-protocol backend split**
- `src/domyn_swarm/platform/protocols.py` defines two `Protocol` interfaces that everything
  else implements: `ServingBackend` (`create_or_update`, `wait_ready`, `delete`,
  `ensure_ready`, `status`) manages the life of an inference endpoint; `ComputeBackend`
  (`submit`, `wait`, `cancel`, `probe`, plus `default_python`/`default_image`/
  `default_resources`/`default_env` via a `DefaultComputeMixin`) manages the life of a job
  that targets that endpoint. Both use opaque `ServingHandle`/`JobHandle` value objects and
  standardized `ServingPhase`/`JobStatus` enums so callers never touch platform-specific
  types.
- `Deployment` (`deploy/deployment.py`) is a thin composition of one `ServingBackend` + one
  `ComputeBackend`: `up()` creates+waits for the endpoint, `run()` submits a job against it,
  `down()` tears it down. This is a clean, minimal pattern for decoupling "where inference
  runs" from "how batch jobs are scheduled against it" — deliberately reusable beyond Slurm.
- Two backend pairs are implemented today: **Slurm** (`backends/serving/slurm.py` +
  `backends/compute/slurm.py`, using `srun` inside a load-balanced allocation) and
  **DGX Cloud Lepton** (`backends/serving/lepton.py` + `backends/compute/lepton.py`, via the
  `leptonai` Python SDK, an optional extra). Adding a new platform means implementing the two
  protocols, not touching the orchestration core.

**Orchestrator: `DomynLLMSwarm`**
- `core/swarm.py` defines `DomynLLMSwarm`, a Pydantic `BaseModel` used as a context manager
  (`__enter__`/`__exit__` bring the endpoint up/down). It owns: job submission
  (`submit_job`, `submit_script`), job lifecycle (`wait_job`, `cancel_job`,
  `refresh_job_status`), local persistence (`_persist`, `from_state` — a swarm can be
  rehydrated later from a saved name), and `status()`.
- Every job submission is tracked in a local SQLite state DB: `_record_job_submission` /
  `_update_job_submission` persist name, command, resources, kind, status, external ID
  (Slurm job/step ID or Lepton job ID), and log paths — i.e. Domyn Swarm keeps its own
  durable job audit trail independent of the underlying scheduler, and `refresh_job_status`
  can re-probe the backend to reconcile it.
- `create_swarm_pool` (used in `examples/api/swarm_launch.py`) launches multiple
  `DomynLLMSwarm` instances concurrently (e.g. two independent replicas/configs), and jobs
  can be submitted `detach=True` to run as background child processes, with the caller
  later `waitpid`-ing on the returned PIDs — a simple fan-out pattern for parallel swarms.

**Config: auto-computed resource allocation**
- `config/swarm.py`'s `DomynLLMSwarmConfig` (Pydantic model) has a
  `validate_resource_allocations` model validator that derives `nodes`, `cpus_per_task`,
  and `replicas_per_node` from `replicas`, `gpus_per_replica`, and `gpus_per_node` when not
  given explicitly — e.g. `nodes = ceil(replicas / replicas_per_node)` or, for multi-GPU
  multi-node replicas, `ceil((replicas * gpus_per_replica) / gpus_per_node)`. This is the
  concrete mechanism behind the "just write gpus_per_replica/replicas in YAML" quickstart
  experience.
- `config/plan.py`'s `PlanBuilder` normalizes this into a `DeploymentPlan`
  (serving+compute backend instances plus per-backend specs) and `DeploymentContext`
  (normalized fields shared across serving and compute) — a single place where
  backend-specific defaults (default container image, default Python interpreter, default
  resources/env) get resolved before either backend is touched.

**Jobs: `SwarmJob` abstract base + checkpointed execution**
- `jobs/api/base.py` defines `SwarmJob(abc.ABC)`. User code implements one method:
  `async def transform_items(items: list[Any]) -> list[Any]` (pure, order-preserving). A
  `transform_streaming` variant supports checkpoint-as-you-go without retaining all outputs
  in memory. The constructor takes ~20 parameters covering input/output column naming,
  concurrency (`max_concurrency`), `retries`, `timeout`, `checkpoint_interval`, an
  `OutputJoinMode` (e.g. `APPEND`), and a pluggable `data_backend`.
- `jobs/base.py` (the module named in the original README) is now a **deprecated
  compatibility shim** re-exporting from `jobs/api/base.py` with a `DeprecationWarning` —
  the legacy `transform(df)`-based job shape has been fully replaced by the
  `transform_items(items)` contract.
- Checkpointing is a separate, swappable concern (`checkpoint/store.py`): a
  `CheckpointStore[T]` protocol (`prepare`, `flush`, `finalize`) with two implementations —
  `ParquetShardStore` (writes monotonically-named Parquet shards to local or cloud URIs via
  `fsspec`, tracks already-completed IDs to support resume, and merges shards on
  `finalize()`) and `InMemoryStore` (no disk I/O, for tests/small jobs).
- Data backends are pluggable via a registry (`data/backends/registry.py`): pandas
  (default), optional Polars, optional Ray — so the same `SwarmJob` can run over different
  DataFrame engines depending on scale.

**Runtime health: watchdog + collector**
- `runtime/watchdog.py` runs as a per-replica supervisor process: it spawns the actual vLLM
  child process, polls its HTTP health endpoint (`_check_http`) and, for Ray-backed
  multi-node replicas, probes Ray cluster health and expected worker/tensor-parallel
  capacity (`_ray_cluster_ok`, `_ray_capacity_ok`). A hardcoded `RAY_FATAL_EXIT_CODE = 190`
  distinguishes non-retryable Ray failures from transient ones (`_should_restart` decides
  whether to respawn based on exit code).
- Replica state (`ReplicaState` enum) and failures are reported via `send_status()` to a
  separate **collector** process, described in `AGENTS.md` as "single writer to
  `watchdog.db`" — i.e. watchdogs never write the SQLite DB directly, avoiding
  multi-writer contention; only the collector does, and `domyn-swarm status` reads from it.
  `build_fail_reason` classifies failures from log tails into a human-readable reason plus
  a `retryable` boolean.
- This is a real, if minimal, self-healing mechanism for long-running Slurm-allocated vLLM
  replicas — not just "start it and hope," which matters on HPC clusters where a node/GPU
  fault shouldn't require a human to notice and manually resubmit.

**State & CLI**
- Two SQLite databases: a global `swarm.db` (`${DOMYN_SWARM_HOME:-~/.domyn_swarm}/swarm.db`)
  for swarm/job records, and a per-swarm `watchdog.db` under
  `.../swarms/<swarm-name>/` for replica health. Schema changes go through Alembic
  migrations with an auto-upgrade step that runs on every CLI invocation (skippable via
  `DOMYN_SWARM_SKIP_DB_UPGRADE=1`), guarded by a threading lock (per changelog) to avoid
  concurrent-upgrade races.
- The CLI (`cli/main.py`, Typer) uses a `LazyGroup` that defers importing heavy subcommand
  modules (job management, swarm lifecycle) until actually invoked, plus lazy proxies
  (`_LazyDomynLLMSwarm`, `_LazySwarmStateManager`, `_LazyLogger`) — purely a startup-latency
  optimization (per recent changelog entries: "defer heavy imports off the swarm-load
  path"), notable mainly as evidence of active performance-focused maintenance.
- Commands include `up`/`down` (swarm lifecycle), `status` (table via Rich TUI or stable
  JSON via `-o json`), and a `job` subcommand group (`submit`, `submit-script`, `status`,
  `cancel`, `list` — added incrementally through v0.26–v0.29 per CHANGELOG.md, including
  job persistence with external-ID tracking and idempotent cancellation).

**Maturity signals**
- `pyproject.toml`: version `0.29.0`, `Development Status :: 3 - Alpha`, Python
  `>=3.10,<3.14`, Apache-2.0. Two named maintainers with `@domyn.com` addresses (Federico
  D'Ambrosio, Alessandro Rognoni) — a small, identifiable internal team, not a broad
  open-source community project (1 fork, 23 stars at time of writing).
- CHANGELOG.md shows fast, incremental delivery: Ray backend support, Polars backend,
  stable sharding strategies (`id` vs `index` mode), sharded/resumable checkpoint stores,
  the watchdog/collector health system, and full job CRUD with JSON status output were all
  added across versions v0.25.0–v0.29.0 (Jan–Jun 2026) — consistent with a tool under active
  internal dogfooding at Domyn rather than a one-off open-source drop.
- Still not published to PyPI as of this checkout (per AGENTS.md/README); installed via
  `uv`/`pip` directly from the GitHub repo at a pinned tag.

## CF relevance

The `ServingBackend` / `ComputeBackend` protocol split, composed by a single `Deployment`
object, is a directly reusable pattern for any platform wanting to decouple "stand up an
inference/agent endpoint" from "schedule work against it" across heterogeneous compute
(here: Slurm vs. Lepton; for CF, potentially Diego/CAPI vs. some GPU-scheduling backend).
Three other pieces are worth studying as concrete, load-bearing reference implementations
rather than abstract patterns: (1) the **watchdog/collector split** — one writer to a local
health-status store, workers only report — is a simple, robust pattern for supervising
long-running GPU workloads without database contention; (2) the **resumable, sharded
Parquet checkpoint store** with monotonic shard naming and "already-done ID" tracking is a
concrete answer to "how do you make a long batch job restart-safe"; (3) **local SQLite job
persistence independent of the underlying scheduler**, with a `refresh_job_status`
reconciliation path, is a lightweight pattern for a platform to keep its own durable
job/audit record without depending entirely on the backend's own state (relevant to
audit/observability-governance concerns raised in the broader agentic-workload research).
Note the scope limit: none of this is agent orchestration (no planning, tool use, or
multi-agent coordination) — it is HPC batch-inference plumbing, so its relevance is to the
"run the model reliably at scale" layer, not the "agent decides what to do" layer.

## Open questions

- How does the watchdog/collector health system behave across a full node failure (not
  just process crash) — does Slurm's own requeue interact with domyn-swarm's restart
  logic, or can they conflict (e.g. double-restart)?
- The `ParquetShardStore` resume logic depends on stable ID columns across runs — what
  happens if the input DataFrame's row order or ID scheme changes between a failed run and
  its resume attempt (partial-shard consistency wasn't verified in this pass)?
- Is there a production user of the `ray` data-backend / Ray-backed multi-node serving path
  outside Domyn's own Colosseum cluster, or is Ray support Slurm-specific tooling that
  wouldn't transfer to a non-HPC scheduler?
- The two named maintainers and Apache-2.0 license suggest Domyn intends this as a genuine
  reusable open-source tool (vs. a marketing artifact) — is there any public roadmap or
  issue tracker activity indicating outside contributions, or is it effectively
  single-vendor maintained?
- How (if at all) does Domyn Swarm relate to the proprietary "Platform" product marketed on
  domyn.com for building/orchestrating AI Agents — is Swarm the inference substrate
  underneath that product, a separate internal tool, or unrelated?
