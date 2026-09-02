---
title: "CrewAI — Role-Based Crews and Event-Driven Flows"
author: Ruben Koster (@rkoster)
date: 2026-08-10
tags: [orchestration, inter-agent-comms, observability-governance, runtime-lifecycle, ecosystem-survey]
cf_areas: []
status: draft
sources:
  - https://github.com/crewAIInc/crewAI
  - https://docs.crewai.com/en/introduction
  - https://docs.crewai.com/en/concepts/processes
  - https://docs.crewai.com/en/concepts/flows
  - https://docs.crewai.com/en/concepts/checkpointing
  - https://docs.crewai.com/en/concepts/memory
  - https://docs.crewai.com/en/mcp/overview
  - https://docs.crewai.com/en/observability/overview
  - https://docs.crewai.com/en/observability/tracing
  - https://docs-platform.crewai.com/platform/en/introduction
ratings:
  platform-impact:
    value: 78
    note: 'Initial review of CrewAI — Role-Based Crews and Event-Driven Flows: its subject and tags indicate how broadly the capability could affect an agentic platform.'
  maturity:
    value: 76
    note: 'Initial review of CrewAI — Role-Based Crews and Event-Driven Flows: this score reflects the amount of established external practice visible in the note.'
  novelty:
    value: 62
    note: 'Initial review of CrewAI — Role-Based Crews and Event-Driven Flows: this score reflects how distinct or emerging the approach appears in the current landscape.'
  actionability:
    value: 66
    note: 'Initial review of CrewAI — Role-Based Crews and Event-Driven Flows: this score reflects how readily the material could guide a focused experiment or follow-up.'

---

## Summary

CrewAI is a standalone, MIT-licensed Python framework (not built on LangChain) for
orchestrating multi-agent AI systems, maintained by crewAI Inc., a VC-backed startup rather
than a foundation. It has two complementary orchestration primitives: **Crews** — teams of
role-playing autonomous agents (role/goal/backstory) that collaborate via sequential or
manager-led hierarchical task delegation — and **Flows**, a newer, deterministic, event-driven
orchestration layer (`@start`/`@listen`/`@router` decorators over Pydantic or dict state)
added specifically to give developers fine-grained control that pure agent-to-agent Crew
autonomy lacked. The current guidance is "start with a Flow, drop into a Crew for sub-tasks
that need autonomous collaboration." The open-source library ships a broad production feature
set — MCP client tool integration, built-in A2A protocol events for both client and server
roles, a unified memory system, and file/SQLite-based checkpointing with fork/resume — while
commercial depth (hosted deployment, no-code builder, tracing dashboard, RBAC) lives in the
separately licensed "CrewAI AMP" SaaS platform.

## Key findings

- **License, governance, standalone status**: MIT-licensed, developed by crewAI Inc. (a
  commercial startup, not a foundation-governed project). The README's FAQ states explicitly:
  "CrewAI is a standalone Python framework with its own primitives for agents, tasks, crews,
  flows, tools, and orchestration" — built independently of, not as a wrapper around,
  LangChain.
- **Scale/maturity signals**: ~56.9k GitHub stars, 8.1k forks, 2,732+ commits, published to
  PyPI as `crewai`, with claims of "100,000+ developers certified" via associated courses —
  indicating a mature, widely-adopted project.
- **Role-based agent model**: an `Agent` is defined by `role`, `goal`, and `backstory`
  (natural-language persona fields shaping prompting), plus `tools`, optional `memory`, and
  LLM config. Agents are grouped into a `Crew` with a list of `Task` objects (each with
  `description`, `expected_output`, and an assigned agent).
- **Two Crew orchestration "Processes"**: `Process.sequential` runs tasks in strict list
  order, piping each task's output as context into the next. `Process.hierarchical` requires a
  `manager_llm` or custom `manager_agent`; the manager is not pre-assigned tasks but
  dynamically plans, delegates to whichever agent is best suited, and validates/reviews
  outputs — closely modeling a human management hierarchy.
- **Flows as the newer, deterministic orchestration layer**: added to address Crews' lack of
  fine-grained control. A `Flow` subclass uses `@start()` for entry points, `@listen(x)` to
  trigger on completion of method `x` (or router labels), `@router(x)` for conditional
  branching, and `or_()`/`and_()` combinators for multi-condition triggers. Flows can hold
  unstructured dict state or structured Pydantic `BaseModel` state, both auto-assigned a UUID.
  A Flow step can instantiate and run one or more Crews in sequence/parallel, with the Crew's
  result flowing back into Flow state for downstream routing — "Flow is the backbone/manager;
  Crew is the intelligence doing heavy lifting per step" is the officially recommended
  production architecture.
- **Real durability/crash-recovery mechanism**: the `@persist` decorator (class- or
  method-level) auto-saves Flow state to SQLite after each step, enabling resume-by-id or
  fork-from-snapshot. More broadly, a first-class **Checkpointing** system applies to `Crew`,
  `Flow`, and even a single `Agent`: event-driven (default `task_completed`, or any of ~80
  granular event types including `llm_call_completed`), pluggable storage (`JsonProvider` or
  `SqliteProvider` with WAL), `max_checkpoints` pruning, a `crew.fork()` API for branch
  experiments, and a terminal UI (`crewai checkpoint`) to browse/resume/fork visually — a
  genuine, documented durable-execution mechanism, not merely "none built-in" as might be
  assumed of a lighter-weight framework.
- **A2A protocol support is real and fairly deep**: the Checkpointing event catalog reveals
  extensive built-in A2A support — `a2a_delegation_started/completed`,
  `a2a_conversation_started/completed`, `a2a_polling_started/status`,
  `a2a_push_notification_registered/received/sent/timeout`, `a2a_streaming_started/chunk`,
  `a2a_agent_card_fetched`, `a2a_authentication_failed`, `a2a_server_task_started/completed`,
  `a2a_parallel_delegation_*`, `a2a_transport_negotiated` — indicating both A2A client
  (delegating to remote agents, polling, push notifications, streaming) and A2A server
  (exposing its own agents/tasks via agent cards) roles are natively implemented, though no
  single canonical "A2A overview" doc page was found during this research (see `a2a-protocol.md`
  for the protocol itself).
- **MCP tool integration, first-class in two ways**: a simple DSL — `Agent(mcps=[...])`
  accepting string references (remote HTTPS URLs, optionally scoped to one tool, or
  "connected" catalog integrations like Snowflake/Stripe) or structured
  `MCPServerStdio`/`MCPServerHTTP`/`MCPServerSSE` configs with tool filtering and
  connection-timeout controls — and an advanced `MCPServerAdapter` context-manager for manual
  lifecycle control. All three MCP transports are supported, with graceful degradation on
  unreachable servers.
- **Memory recently redesigned into a single unified system**: replacing separate short/long-
  term/entity memory types with one `Memory` class that uses an LLM to infer scope
  (hierarchical filesystem-like paths), categories, and importance on save; supports
  composite-scored recall blending semantic similarity, recency decay, and importance;
  "deep" (multi-step, LLM-guided) vs. "shallow" (pure vector) recall depths; automatic
  consolidation/deduplication of near-duplicate facts; per-agent private scopes and
  multi-scope read-only views for isolation/sharing patterns; and non-blocking background
  writes. Default storage is local LanceDB with a pluggable custom backend.
- **Observability split between commercial dashboard and third-party integrations**: built-in
  `tracing=True` reports to the CrewAI AMP hosted dashboard (agent decisions, task timeline,
  tool/LLM calls, token/cost metrics) — tied to a commercial account. Separately, CrewAI
  documents integrations with LangDB, OpenLIT (OpenTelemetry-native), MLflow, Langfuse,
  Langtrace, Arize Phoenix, Portkey, Opik, and Weave. No native vendor-neutral OpenTelemetry
  GenAI semantic-convention export from the OSS library itself (unlike Google ADK,
  `google-adk.md`) — OTel-style observability is reached indirectly via OpenLIT.
- **OSS library + separately-branded commercial platform**: the core `crewai` package is a
  plain pip/uv-installable library, self-hostable with zero required cloud dependency
  (`crewai create crew`/`crewai run`). "CrewAI AMP" (Agent Management Platform, formerly
  "Enterprise") is the commercial layer: managed deployment via GitHub/CLI, REST API access to
  deployed crews, webhook event streaming, a "Tool Repository," a no-code "Crew Studio"
  builder, RBAC, automation triggers, and the tracing dashboard — offered as SaaS or
  on-premise, with a free tier ("Crew Control Plane").
- **Telemetry defaults**: CrewAI collects anonymous, non-content OSS telemetry by default
  (version, OS, agent/task counts, tool names) — explicitly excludes prompts/backstories/
  outputs unless the user opts in. Disable via `OTEL_SDK_DISABLED=true`.

## CF relevance

CrewAI's Flows-orchestrate-Crews pattern is a useful, concrete illustration of a recurring
theme across this research set: pairing a deterministic, event-driven control layer with an
autonomous, LLM-driven collaboration layer for the parts of a workflow that benefit from
agent judgment — directly comparable to how Google ADK layers graph workflows over
collaborative sub-agent delegation, and how Microsoft Agent Framework layers explicit
workflow graphs over its Harness. CrewAI's checkpoint-and-fork model (branch experiments from
any saved state) is also a distinctive, lightweight alternative to Temporal's full
replay-based durability or Dapr's actor/state-store model, worth comparing directly for a
CF-native durable-execution story that doesn't require a separate service (SQLite-file-based
checkpointing has minimal infrastructure requirements). The split between a genuinely
open-source, self-hostable core and a separately licensed commercial platform (AMP) for
hosting/tracing/RBAC is also a familiar SaaS-wrapper-around-OSS pattern CF should expect to
see repeated across this ecosystem.

## Open questions

- CrewAI's checkpoint-and-fork model requires no external durability service (just a SQLite
  file or JSON directory) — is this a lighter-weight, CF-app-instance-friendly durability
  pattern worth prototyping against, compared to the heavier Temporal/Dapr substrates covered
  elsewhere?
- How mature/spec-compliant is CrewAI's A2A implementation relative to Google ADK's or
  Strands' — worth a follow-up deep-dive directly against the CrewAI source (`crewai/a2a/`
  module) rather than inferring from the checkpointing event catalog alone?
- Is CrewAI's hierarchical `manager_agent` process (dynamic task planning/delegation by an
  LLM manager) meaningfully different from Google ADK's `task`-mode sub-agent delegation, or
  a similar pattern under different naming?
- Given the OSS/commercial split (core library vs. AMP), would a CF-native agent platform
  want to offer the missing pieces (hosted deployment, tracing dashboard, RBAC) as bindable
  platform services, letting the CrewAI OSS library remain purely a workload dependency?
