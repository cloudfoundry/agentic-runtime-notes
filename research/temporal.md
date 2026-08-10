---
title: "Temporal — Durable Execution as a Standalone Service"
author: Ruben Koster (@rkoster)
date: 2026-08-10
tags: [orchestration, runtime-lifecycle, ecosystem-survey]
cf_areas: []
status: draft
sources:
  - https://github.com/temporalio/temporal
  - https://docs.temporal.io/evaluate/why-temporal
  - https://docs.temporal.io/evaluate/understanding-temporal
  - https://docs.temporal.io/workflows
  - https://docs.temporal.io/temporal-service
  - https://docs.temporal.io/temporal-service/persistence
  - https://github.com/temporalio/temporal/blob/main/LICENSE
  - https://github.com/temporalio/sdk-python/tree/main/temporalio/contrib/openai_agents
  - https://temporal.io/blog/durable-flexible-multi-agent-systems
  - https://temporal.io/cloud
---

## Summary

Temporal is an MIT-licensed durable execution / workflow orchestration engine (22.2k GitHub
stars, forked from Uber's Cadence, developed by Temporal Technologies Inc.). Applications
write ordinary code as **Workflows**; Temporal persists an append-only **Event History** for
each Workflow Execution and replays it on failure or resumption to reconstruct exact
pre-crash state — a fundamentally different durability mechanism from Dapr's actor/state-store
checkpointing. Unlike Dapr, Temporal is not a sidecar: it's a standalone, centrally-run service
that stateless client **Workers** connect to over the network, and its product surface is
narrowly workflow/durable-execution (no built-in pub/sub, generic state store, or service
invocation building blocks). It is being actively positioned and used for durable AI agent
loops, with official SDK integrations for the OpenAI Agents SDK, Google ADK, and LangGraph.

## Key findings

- **Core building blocks**: a **Workflow** is deterministic orchestration code (the sequence
  of steps); an **Activity** is a unit of work that touches the outside world (API calls, DB
  writes, LLM calls) and gets automatic retries; a **Worker** is an application process that
  polls one or more named **Task Queues** for Workflow/Activity tasks to execute; **Signals**
  push async events into a running Workflow, **Queries** read its state synchronously.
  ([docs.temporal.io/workflows](https://docs.temporal.io/workflows))
- **Durability model — event history + replay, not checkpointing**: every Workflow Execution
  emits Commands and processes Events, recorded in an ordered, append-only Event History
  persisted by the Temporal Service. On resume, Temporal does **not** restore a memory
  snapshot — it re-runs the Workflow code from the start (or from a cached point), replaying
  recorded events so the code deterministically arrives back at the same state. This is why
  Workflow code must avoid non-deterministic operations (`Date.now()`, raw randomness, direct
  network calls) — those must go through Activities or replay-safe context APIs. This is a
  distinct model from Dapr Workflows, which layers durability on the Dapr Actor runtime with
  state persisted via a pluggable **state store** component; Temporal's "state" *is* the event
  history itself. Long-running loops (e.g., an agent that runs indefinitely) must call
  **Continue-As-New** periodically to start a fresh Workflow Execution and bound Event History
  growth — documented as a concrete lesson in Temporal's own multi-agent demo, where "the
  driver loops never stop" and needed Continue-As-New to run for days without unbounded
  history. ([docs.temporal.io/workflows](https://docs.temporal.io/workflows),
  [temporal.io/blog/durable-flexible-multi-agent-systems](https://temporal.io/blog/durable-flexible-multi-agent-systems))
- **Architecture vs. Dapr — no sidecar**: Temporal is a standalone, clustered **Temporal
  Service** (Frontend/History/Matching/Worker internal services + a persistence store —
  Cassandra, MySQL 8+, PostgreSQL 13+, or SQLite for dev-only — plus an Elasticsearch or
  SQL-based Visibility store) that your application's SDK Client and Worker processes talk to
  over the network. Workers *poll* Task Queues outbound; they don't need any inbound network
  exposure and can run anywhere (containers, batch jobs, laptops). This is architecturally
  distinct from Dapr's per-instance sidecar exposing pluggable building blocks (state, pub/sub,
  service invocation, actors, workflow) alongside each app — Temporal has no sidecar and no
  building blocks beyond durable Workflows/Activities/Signals/Queries; everything else (queuing,
  pub/sub, generic state) is explicitly *not* Temporal's job, per its own framing ("eliminates
  the need for queues, pub/sub systems, and schedulers" as a *consequence* of Workflow code,
  not a separate building block it exposes). ([docs.temporal.io/temporal-service](https://docs.temporal.io/temporal-service),
  [docs.temporal.io/temporal-service/persistence](https://docs.temporal.io/temporal-service/persistence))
- **Concrete AI-agent orchestration evidence** (not just marketing framing):
  - `temporalio/sdk-python` ships an official `temporalio.contrib.openai_agents` plugin: it
    registers an Activity that executes each OpenAI Agents SDK model call, handles Pydantic
    serialization, propagates OpenAI's own tracing context into OTel, and supports pluggable
    sandboxed code-execution backends (Daytona, local Unix) and MCP servers as first-class
    integration points registered on the Worker.
    ([github.com/temporalio/sdk-python](https://github.com/temporalio/sdk-python/tree/main/temporalio/contrib/openai_agents))
  - A August 2026 Temporal engineering blog post, "Durable, flexible multi-agent systems,"
    walks through running the *same* multi-agent fleet (Fleet/Customer/Dispatch agents) on
    Google ADK, on LangGraph, and on both at once, with Temporal underneath for durability —
    concrete evidence of framework-agnostic positioning, not a single proprietary agent SDK.
    ([temporal.io/blog/durable-flexible-multi-agent-systems](https://temporal.io/blog/durable-flexible-multi-agent-systems))
  - Human-in-the-loop is modeled as a **Signal** the Workflow waits on via
    `workflow.wait_condition(...)` — used both when a human interrupts a running agent
    (approval gate lives in the Workflow, not the LLM) and when an agent's own tool call
    (`ask_human`) suspends execution and waits, potentially for hours, for an operator response.
    Because this is a durable Signal rather than an in-memory callback, the wait survives
    Worker restarts/crashes.
  - The same post reports a concrete operational pitfall specific to agents: putting LLM
    reasoning and other Activities (e.g., driver navigation) on one shared Task Queue let slow
    inference calls starve other work; splitting into separate Task Queues fixed it — a
    practical detail future adopters would need to plan for.
- **License and governance**: confirmed MIT ([LICENSE](https://github.com/temporalio/temporal/blob/main/LICENSE),
  copyright Temporal Technologies Inc. and the original Uber Technologies copyright from the
  Cadence fork). 22.2k stars, 1.8k forks, 9,600+ commits — actively developed. Unlike Dapr
  (a CNCF project), Temporal is **not** stewarded by a vendor-neutral foundation; its sole
  steward is Temporal Technologies Inc., a venture-backed company that also sells **Temporal
  Cloud**, a fully-managed hosted version of the same server. I did not find evidence in this
  research pass of Cloud-only forked features fragmenting the open-source core (the OSS
  `temporal` repo appears to be what Cloud runs), but I did not do an exhaustive feature-parity
  audit, so this is not a confirmed absence — treat it as unverified either way. This open-core
  shape (single-vendor OSS + hosted commercial offering) is structurally similar to Dapr's
  relationship with Diagrid, worth noting as a parallel rather than a difference.
- **Multi-tenancy primitive**: Temporal has a **Namespace** concept (visible via
  `temporal operator namespace list` in the CLI) as its isolation boundary for Workflows/Task
  Queues within one Temporal Service — I did not dig deep enough to characterize its isolation
  guarantees (e.g., whether it's suitable as a hard multi-tenant boundary or more of a logical
  grouping), so this is flagged as an open question below rather than a finding.

## CF relevance

Temporal's polling-Worker model (no inbound network exposure needed, Workers can be any
process) is a notably different operational shape than a sidecar-per-instance and might map
more naturally onto CF's existing app/process model — a CF app could simply *be* a Temporal
Worker without needing a co-located sidecar process. Continue-As-New as a pattern for bounding
state growth in long-running agent loops seems like a generally useful idea regardless of which
durable-execution substrate CF ends up considering. On the other hand, Temporal requires
operating (or paying for) a separate, stateful, clustered service with its own persistence and
visibility stores — a heavier platform dependency than a sidecar, and one CF would need to
either run centrally (raising multi-tenancy/isolation questions) or provision per-space/org.
Not yet clear how this trades off against Dapr's model where the "workflow engine" rides along
with the app itself.

## Open questions

- How isolated are Temporal Namespaces in practice — could CF spaces map 1:1 to Namespaces on
  a shared Temporal Service, or would noisy-neighbor concerns (shared Task Queues, shared
  History/Matching service capacity) push toward a Temporal Service per foundation/space?
- Workflow code must be deterministic (no direct I/O, wall-clock, or randomness in the Workflow
  body) — how much of a developer-experience burden is this for typical CF app authors compared
  to Dapr's less constrained programming model, and would a buildpack/framework need to enforce
  or paper over this?
- Would CF operate its own self-hosted Temporal Service (with attendant Cassandra/MySQL/Postgres
  + Elasticsearch operational burden), or lean on Temporal Cloud as a managed dependency — and
  what does that imply for CF's preference for vendor-neutral, self-hostable control planes?
- What would authentication between CF app instances (as Workers) and a shared Temporal Service
  look like — mTLS, namespace-scoped API keys, something SPIFFE/SVID-based?
- The OpenAI Agents SDK / ADK / LangGraph integrations are framework-level; is there an
  equivalent low-level pattern CF could adopt without committing an app to a specific agent
  framework?
