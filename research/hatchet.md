---
title: "Hatchet — Postgres-Backed Durable Task Queue, Marketed for AI Agents"
author: Ruben Koster (@rkoster)
date: 2026-08-11
tags: [runtime-lifecycle, orchestration, observability-governance, ecosystem-survey]
cf_areas: []
status: draft
sources:
  - https://hatchet.run/
  - https://hatchet.run/use-cases/ai-agents
  - https://hatchet.run/use-cases/durable-execution
  - https://github.com/hatchet-dev/hatchet
  - https://docs.hatchet.run/v1/tasks
  - https://docs.hatchet.run/v1/durable-tasks
  - https://docs.hatchet.run/cookbooks/durable-tasks-vs-dags
  - https://docs.hatchet.run/v1/durable-sleep
  - https://docs.hatchet.run/v1/durable-event-waits
  - https://docs.hatchet.run/v1/rate-limits
  - https://docs.hatchet.run/v1/concurrency
  - https://docs.hatchet.run/v1/opentelemetry
  - https://docs.hatchet.run/self-hosting
---

## Summary

Hatchet is an MIT-licensed, open-source orchestration engine for background tasks, durable
workflows, and — increasingly, per its own marketing — AI agents, built by Hatchet
Technologies (a 2023 YC W24 startup). Its central architectural differentiator versus peers
like Temporal (covered in `temporal.md`), Celery, and BullMQ is that it uses **Postgres as the
sole durability layer** for both task execution history and observability data, rather than a
dedicated event store or a Redis/RabbitMQ broker — a deliberate simplicity/self-hostability
trade-off against raw throughput, which Hatchet's own docs state explicitly. It ships SDKs for
Python, TypeScript/Node, Go, and Ruby, is multi-tenant by default, and is offered both
self-hosted (Docker/Kubernetes) and as a managed "Hatchet Cloud" service — an open-core model.

## Key findings

- **License, governance, origin**: MIT-licensed, fully open source (~7.7k GitHub stars, 466
  forks). Built by Hatchet Technologies, a 2023 Y Combinator (W24 batch) startup founded by
  Alexander Belanger (ex-CTO, Porter) and Gabe Ruttner (ex-CTO, ClearMix) — both YC alumni
  from earlier (S20) companies. Based in New York City, team size approximately 7.
- **Postgres-backed durability is the headline differentiator**: Hatchet's own README states
  it uses Postgres as the durability layer for "both the task runtime and the observability
  system, making it particularly easy to self-host" — unlike Temporal (custom persistence plus
  event history, requiring Cassandra/MySQL/PostgreSQL plus a separate Elasticsearch/SQL
  visibility store) or Celery/BullMQ (Redis/RabbitMQ broker with no durable execution history
  at all). This meaningfully lowers the operational footprint of self-hosting relative to
  Temporal, at a stated cost in raw throughput.
- **The durability/throughput trade-off is explicit in Hatchet's own docs**: "Hatchet is a
  *durable* task queue... it persists the history of all executions... Hatchet's durability
  features add some overhead: while Hatchet has been load-tested up to 10k tasks/second, it
  consumes more resources than a system built on Redis or RabbitMQ." This is a rare instance
  of a vendor stating its own performance trade-off directly rather than only in marketing
  comparisons.
- **SDKs and worker model**: official, idiomatic (no DSL/YAML) SDKs for Python, TypeScript/
  Node.js, Go, and Ruby — notably **no Rust SDK**, despite Hatchet's engine itself being
  written in Rust/Go internally. Workers are ordinary long-lived processes deployable on
  Kubernetes, Docker, ECS, Cloud Run, or PaaS-style targets (Porter, Railway, Render); they
  connect *out* to the Hatchet engine, which assigns tasks to worker "slots" (a push model to
  registered workers, not simple polling of a queue).
- **Core primitives**: **Tasks** (plain functions) composed into DAG-based **workflows**, plus
  a distinct **durable tasks** primitive for fault-tolerant long-running logic — Hatchet's docs
  explicitly separate "DAGs" (simpler, dependency-graph pipelines) from "durable tasks"
  (replay-recoverable, described as "a drop-in replacement for Temporal or DBOS workflows") and
  provide guidance on when to use which rather than treating them as one thing. Retries with
  exponential backoff, cron jobs, scheduled (one-time future) runs, event-based triggers, and
  webhook-based triggering are all first-class.
- **Durable execution model is a hybrid, not classic deterministic replay**: pause/resume is
  implemented via "durable sleep" and "durable event waits" rather than Temporal-style
  full-history deterministic code replay (`temporal.md`) — closer in spirit to Dapr Workflow's
  activity-level durability (`dapr.md`) than to Temporal's replay-from-start model, though the
  exact mechanics of Hatchet's durable-task recovery weren't independently verified against
  source in this research.
- **Concurrency and rate limiting are marketed, first-class differentiators**: static rate
  limiting (for third-party API quotas) or dynamic per-user/per-tenant limits, "fair
  scheduling" via concurrency policies keyed on dynamic values (preventing one tenant from
  monopolizing shared workers), task priority levels, and worker-slot caps on in-flight work
  per worker. A customer testimonial specifically credits this as differentiating Hatchet from
  competitors treating concurrency control as an afterthought.
- **Human-in-the-loop / pause-resume is marketed directly on the homepage**: "Human-in-the-loop
  built in, pause and resume at any point," implemented through durable sleep, event waits, or
  a combination of both, plus built-in eventing described specifically for agent
  human-in-the-loop signaling and streaming responses — the same shape of feature seen in
  Temporal's Signals, Dapr's `wait_for_external_event`, and LangGraph's `interrupt()`
  (`langgraph.md`), but with no inbound network requirement described any differently from
  those.
- **Multi-tenant by default**: Hatchet is explicitly "multi-tenant by default, so a single
  Hatchet instance can support multiple teams," with centralized user/worker/tenant management
  in one place, and tenant-scoped fair scheduling tied directly into the concurrency-control
  feature above. The exact isolation mechanism (schema-per-tenant, row-level `tenant_id`, or
  separate databases) was not detailed in the marketing docs reviewed and would need a source
  dive to compare directly against the multi-tenancy caveats already identified for Dapr
  (shared placement/sentry blast radius, mTLS-dependent namespace verification) — worth
  treating as an open question rather than an established comparison.
- **AI-agent positioning is a primary go-to-market pillar, not incidental**: a dedicated
  "AI Agents" use-case page markets "durable agents by default," claims "processing over 100
  million tasks/day for AI-first companies," and cites customer workloads including LLM
  document-ingestion pipelines, 30-minute-long agentic financial-advisory workflows, and
  embedding pipelines for RAG retrieval. Notably, **no documented first-class integration with
  LangChain/LangGraph or CrewAI was found** — Hatchet's story is "write your agent logic as
  Hatchet tasks," positioning it as a substrate agent frameworks could be built on rather than
  a plugin/adapter for existing frameworks, in contrast to Temporal's and Dapr's documented
  official integrations with the OpenAI Agents SDK and Google ADK.
- **Deployment is open-core**: self-hosted via a single CLI install script backed by local
  Docker, or Docker Compose/Helm for production; Hatchet Cloud is the managed offering with
  autoscaling, pay-as-you-go pricing, multi-region deployment, SSO, and enhanced observability
  not present (or less polished) in the self-hosted OSS edition.
- **Observability**: a built-in real-time web dashboard for workflow/task run status, traces,
  and logs, with one-click replay of failed runs; a built-in OpenTelemetry collector emitting
  traces/spans for every task and workflow execution (or forwarding to external OTEL
  destinations, see `opentelemetry-genai.md`); and a native Prometheus metrics endpoint.
- **Adoption signals**: ~7.7k GitHub stars / 466 forks; Hatchet Cloud's own marketing claims
  "374M tasks run daily" and "50+ active projects." Named customers/testimonials include
  Cursor, Greptile, Motion, and roughly a dozen smaller AI-first startups — indicating real but
  still early-stage, developer-tool-adjacent adoption rather than large-enterprise usage.

## CF relevance

Hatchet is a useful third data point (alongside Temporal and Dapr Workflows, both already
covered in this research set) on how much infrastructure a durable-execution substrate
actually requires: its Postgres-only durability model is a meaningfully lighter operational
footprint than Temporal's dedicated persistence/visibility stores or Dapr's actor-runtime/
placement-service model, at an admitted throughput cost. That trade-off is directly relevant to
the CF-native durable-execution primitive sketched in `durable-tasks-for-cf.md` — Hatchet is
concrete evidence that "durability backed by a single relational database, not a bespoke event
store" is a viable, production-used design point, not just a theoretical simplification. Its
explicit separation of "DAGs" from "durable tasks" as two different primitives with different
guarantees is also a useful naming/scoping precedent if CF ends up wanting to distinguish
lighter dependency-graph pipelines from fully durable, resumable executions. Its lack of any
documented LangGraph/CrewAI integration — despite being marketed hard at AI-agent workloads —
reinforces a pattern already visible elsewhere in this survey: most durable-execution
substrates expect the agent framework's own delegation interface (a checkpointer, a session)
to be adapted to them, rather than shipping the adapter themselves.

## Open questions

- What is Hatchet's actual multi-tenant isolation mechanism (schema-per-tenant, row-level
  `tenant_id`, separate databases), and how does its blast-radius profile compare to the Dapr
  shared-control-plane caveats already identified (see the multi-tenancy discussion referenced
  in `dapr.md`)? This wasn't resolved by marketing docs and needs a source-level look.
- Is a single-Postgres-backed durability model (Hatchet's approach) sufficient at CF-foundation
  scale, or does its stated ~10k tasks/second ceiling make it a poor fit compared to Temporal's
  purpose-built persistence layer for large deployments?
- How exactly does Hatchet's "durable sleep"/"durable event wait" recovery model work
  internally — is it closer to Temporal's full-history replay, or closer to Dapr's
  activity-level checkpointing? The distinction matters for determinism requirements on
  workload code, a concern already raised in `temporal.md` and `langgraph.md`.
- Given Hatchet has no documented LangGraph/CrewAI adapter today, would a CF evaluation of
  Hatchet as a durable-execution substrate need to build that integration itself, the same way
  a CF-native primitive would (`durable-tasks-for-cf.md`) — or is "bring your own agent logic
  as tasks" an acceptable constraint for CF's use case?
- Hatchet's rate-limiting and fair-scheduling-per-tenant features are more developed than
  anything documented for Temporal or Dapr in this research set — is tenant-aware fair
  scheduling a capability CF should expect from any durable-execution substrate it adopts or
  builds, given CF's own multi-tenant org/space model?
