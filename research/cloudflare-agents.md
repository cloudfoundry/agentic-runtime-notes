---
title: "Cloudflare Agents SDK — Agents as Durable Objects (V8-Isolate Isolation)"
author: Ruben Koster (@rkoster)
date: 2026-08-10
tags: [runtime-lifecycle, sandboxing-isolation, autoscaling, inter-agent-comms, ecosystem-survey]
cf_areas: []
status: draft
sources:
  - https://developers.cloudflare.com/agents/
  - https://github.com/cloudflare/agents
  - https://developers.cloudflare.com/agents/runtime/lifecycle/state/
  - https://developers.cloudflare.com/agents/runtime/execution/schedule-tasks/
  - https://developers.cloudflare.com/agents/tools/mcp/
  - https://developers.cloudflare.com/agents/runtime/operations/observability/
  - https://developers.cloudflare.com/agents/runtime/operations/observability/tracing/
  - https://developers.cloudflare.com/durable-objects/
---

## Summary

Cloudflare's Agents SDK (`npm install agents`, MIT-licensed, Cloudflare-owned and not accepting
external contributions) builds "persistent, stateful execution environments for agentic
workloads" on an architecture fundamentally different from every other isolation/runtime model
surveyed in this research set. Its defining bet: **each Agent instance is literally a Durable
Object** — a single-threaded, globally-addressable JavaScript/TypeScript object running in a
V8 isolate, with a private embedded SQLite database, automatic hibernation/wake, and
alarm-backed durable scheduling. There are no containers (contrast Azure Foundry), no
microVMs (contrast AWS AgentCore, `firecracker-microvm.md`), no WASM components (contrast
wasmCloud), and a different concurrency model than Orleans' virtual actors — single-threaded-
per-object with colocated storage, rather than Orleans' turn-based grains backed by pluggable
external storage providers.

## Key findings

- **Ownership/governance**: fully Cloudflare-owned and controlled, MIT-licensed, hosted at
  github.com/cloudflare/agents. Cloudflare explicitly states it is "not accepting external
  pull requests at this time" — a vendor SDK, not a community/foundation project (contrast
  with CNCF-governed Dapr or the .NET Foundation-governed Orleans, `orleans.md`).
- **Core architecture — Agent = Durable Object**: an `Agent` class extends the Durable Object
  primitive directly; deploying one requires a `durable_objects` binding and a
  `new_sqlite_classes` migration entry in `wrangler.jsonc`, exactly like any other DO. There is
  no separate "agent runtime" layered on top — the SDK is a set of ergonomic APIs (`setState`,
  `sql`, `schedule`, `@callable()`, routing helpers) built directly on the DO storage/alarm/RPC
  primitives.
- **Isolation model — V8 isolates, not containers/VMs**: Durable Objects (and Workers
  generally) run in V8 isolates, starting in single-digit milliseconds rather than the seconds
  required for container cold starts, tens-of-seconds for microVMs (AWS AgentCore), or full
  VMs (Azure Foundry). Trade-off: weaker isolation boundary than a VM/microVM (shared-kernel,
  shared-process security model relying on V8 sandboxing) but far higher density and near-zero
  idle cost.
- **State/persistence — built-in per-instance SQLite, no external DB required**: every Agent
  instance gets its own embedded SQLite database, effectively zero-latency because it's
  colocated with the compute. Two APIs: `this.setState()`/`this.state` (JSON-serializable,
  auto-persisted, auto-broadcast to connected WebSocket clients, with lifecycle hooks) and
  `this.sql` (direct template-literal SQL queries). This eliminates the "externalize your
  session state to Redis/Postgres" pattern common in stateless-runtime agent architectures
  (e.g. the OpenAI Agents SDK's `Session` abstraction, `openai-agents-sdk.md`).
- **Hibernation and WebSocket handling**: Durable Objects are evicted from memory after
  ~70–140 seconds of inactivity (no requests, WebSocket messages, or alarms) and rehydrate
  automatically on the next incoming event — state reloads from SQLite transparently. The
  WebSocket Hibernation API keeps connections open across sleep/wake cycles without holding
  the isolate in memory; a `keepAlive()`/`keepAliveWhile()` API exists to explicitly pin an
  agent in memory during long-running work via a 30-second alarm-backed heartbeat.
  Fundamentally different pause/resume timescale than Firecracker's snapshot-to-disk model
  (`firecracker-microvm.md`) — Cloudflare hibernates/rehydrates in-place from SQLite rather
  than snapshotting full VM memory.
- **Scheduling — self-waking agents**: `this.schedule()` supports delayed, Date-based, and
  cron-expression scheduling; `this.scheduleEvery()` supports sub-minute fixed intervals. All
  scheduled tasks are backed by Durable Object alarms and persisted as SQLite rows, surviving
  restarts/hibernation, and are idempotent by default (dedup on callback+payload) — this is
  the mechanism by which an otherwise-hibernating agent wakes itself up later, without any
  external scheduler service.
- **Multi-agent/orchestration patterns**: documented "sub-agents" (parent/child DO composition
  via "facets," nested routing, typed parent lookup) and "agent tools" (running chat-capable
  sub-agents as tools with streaming child timelines), plus a dedicated guide walking through
  sequential, routing, parallel, orchestrator, and evaluator multi-agent patterns (the same
  Anthropic-derived pattern set referenced in the Vercel AI SDK's docs). A separate
  `@cloudflare/codemode` package lets an LLM write executable TypeScript to orchestrate
  multiple tools/sub-agents rather than making individual tool calls.
- **MCP support — client and server, notable ecosystem contributor**: Agents can act as MCP
  clients (`addMcpServer()` + `this.mcp.getAITools()`, with built-in OAuth-state handling
  persisted to the agent's own SQLite) and can be MCP servers themselves. Cloudflare has
  invested specifically in *remote* MCP hosting (as opposed to only local stdio servers),
  reflecting an edge-hosting angle on the MCP ecosystem (`mcp-protocol.md`).
- **A2A protocol**: present but lightly documented — a dedicated `examples/a2a/` example exists
  in the repo, but no standalone conceptual doc page comparable to Azure Foundry's first-class
  A2A support (`azure-hosted-agents.md`, `a2a-protocol.md`).
- **Human-in-the-loop**: delivered via the Workflows integration ("durable multi-step tasks
  with human-in-the-loop approval") layered on top of Cloudflare Workflows, plus a dedicated
  guide for approval workflows with pause/resume; the agents-starter template ships
  human-in-the-loop tool approval out of the box.
- **Deployment/scaling model**: deploy-once, globally distributed — Cloudflare runs agents
  across its global network, scaling to tens of millions of instances with no infrastructure
  to manage, no sessions to reconstruct, no state to externalize. Each Durable Object is
  auto-provisioned geographically close to its first caller and identified by a
  globally-unique name for routing from anywhere. Idle instances cost nothing (hibernation);
  SQLite-backed DOs are available on the Workers Free plan.
- **Observability**: agent-specific tracing layers on top of generic Workers Observability
  (not raw OpenTelemetry SDK support — Workers doesn't support the OTel API directly, though
  span attributes follow OTel GenAI semantic conventions and can be exported via OTLP). Each
  "turn" produces an `invoke_agent` span with nested `chat`, `execute_tool`, and
  `tool_approval` child spans, viewable in a dedicated Agents dashboard tab with session
  replay and waterfall trace views.

## CF relevance

Cloudflare's model is the strongest existing counter-example in this research set to the
assumption that agent runtimes need either a container/VM boundary or an external
state/durability service: by baking per-instance SQLite storage and alarm-based scheduling
directly into the compute primitive, Cloudflare eliminates an entire category of "how do we
keep this agent's state alive between requests" problems that other frameworks solve via
external Sessions/Memory services (OpenAI Agents SDK, `openai-agents-sdk.md`) or full
workflow-replay engines (Temporal, `temporal.md`). This is directly comparable to — and a
useful contrast against — Orleans' virtual-actor model (`orleans.md`): both give "an
addressable, single-threaded, transparently-activated unit of state+compute," but Cloudflare
trades Orleans' storage-provider flexibility for zero-config, colocated persistence and
per-tenant V8-isolate boundaries instead of shared-silo-process grains. For CF, the interesting
question isn't "should CF adopt Durable Objects" but whether CF's own app/process model could
adopt an analogous "cheap, addressable, persistent-by-default compute unit" primitive for
agent workloads specifically, distinct from its general-purpose app hosting model.

## Open questions

- Is a V8-isolate-per-agent isolation boundary (weaker than a VM/microVM, but far cheaper and
  denser) an acceptable trust model for CF-hosted agent workloads that execute
  dynamically-generated or third-party tool code, or does CF's threat model require the
  stronger VM-grade isolation seen in Azure/AWS's managed offerings?
- Cloudflare's hibernate-and-rehydrate-from-SQLite model achieves durability without any
  external database or workflow engine — is this pattern portable to CF's own Diego cell
  model, or does it fundamentally depend on Durable Objects' global routing/addressing layer?
- How would CF's own service-binding model interact with an "agent = durably addressable
  object" primitive, if CF wanted to offer something conceptually similar (e.g., bindable
  per-agent state without requiring an external Redis/Postgres service)?
- Given Cloudflare is not accepting external contributions to this SDK, should CF treat it
  purely as a reference architecture to learn from, or is there a viable integration path
  (e.g., CF apps calling out to Cloudflare-hosted agents via MCP/A2A) worth prototyping?
