---
title: "LangGraph — Low-Level, Pregel-Style Agent Orchestration Runtime"
author: Ruben Koster (@rkoster)
date: 2026-08-10
tags: [orchestration, inter-agent-comms, observability-governance, runtime-lifecycle, ecosystem-survey]
cf_areas: []
status: draft
sources:
  - https://github.com/langchain-ai/langgraph
  - https://docs.langchain.com/oss/python/langgraph/overview
  - https://docs.langchain.com/oss/python/langgraph/graph-api
  - https://docs.langchain.com/oss/python/langgraph/persistence
  - https://docs.langchain.com/oss/python/langgraph/interrupts
  - https://docs.langchain.com/oss/python/langgraph/streaming
  - https://docs.langchain.com/oss/python/langchain/multi-agent
  - https://github.com/langchain-ai/langchain-mcp-adapters
  - https://docs.langchain.com/langsmith/deployment
  - https://docs.langchain.com/langsmith/observability
ratings:
  platform-impact:
    value: 58
    note: 'CF can host LangGraph processes but does not provide its checkpoint store, cross-thread memory, durable pause/resume, or Agent Server packaging as platform services.'
  maturity:
    value: 78
    note: 'LangGraph is a production-oriented LangChain runtime with persistence, interrupts, streaming, MCP integration, and commercial LangSmith deployment options, including a standalone Agent Server.'
  novelty:
    value: 55
    note: 'Applying Pregel-style supersteps, reducer-governed shared state, and boundary checkpoints to agent graphs is a substantial adaptation of established graph-processing and workflow ideas.'
  actionability:
    value: 72
    note: 'The standalone Agent Server provides a bounded buildpack trial using bound Postgres and Redis, with crash recovery testing for non-idempotent nodes and explicit checkpointer/store mapping questions.'

---

## Summary

LangGraph is an MIT-licensed, low-level agent orchestration framework and runtime built by
LangChain Inc., modeling agent logic as a `StateGraph` of nodes and edges over a shared,
reducer-governed state — inspired by Google's Pregel/Apache Beam message-passing model. It
gives developers fine-grained control to mix deterministic code with LLM-driven steps in a
single graph, and is explicitly positioned as *lower-level* than LangChain's own prebuilt
agent abstractions or the newer Deep Agents harness built on top of it. Its headline
capabilities are durable execution via pluggable checkpointers, first-class human-in-the-loop
via `interrupt()`, rich multi-mode streaming, and native MCP tool integration. Production
deployment runs through "LangSmith Deployment" (formerly "LangGraph Platform"), a commercial,
framework-agnostic Agent Server offering cloud, hybrid, self-hosted, and standalone Docker
options — notably, LangGraph has **no first-party A2A protocol support**, a material gap
relative to Google ADK (`google-adk.md`).

## Key findings

- **Positioning within a four-layer LangChain stack**: LangChain's docs describe **Deep
  Agents** (a harness: planning/subagents/filesystem, built on LangGraph) → **LangChain**
  (agent framework: model/tool abstractions, prebuilt agent loops) → **LangGraph**
  (orchestration runtime: durable execution, streaming, HITL, persistence) → **LangSmith**
  (cross-framework tracing/eval/deployment). LangGraph itself is framed as "very low-level" —
  docs recommend LangChain's prebuilt `create_agent` for common tool-calling loops and reserve
  LangGraph for bespoke control flow.
- **Pregel-style superstep execution**: `StateGraph` nodes are plain functions receiving
  `state`, `config`, and a `Runtime` object; edges route via normal (`add_edge`), conditional
  (`add_conditional_edges`), or the `Send` API (map-reduce/fan-out with per-branch state).
  Execution proceeds in discrete "super-steps" — nodes activated by incoming messages run in
  parallel within a superstep; the graph halts when no nodes are active and no messages are
  in transit.
- **State/reducer model**: state schema is a `TypedDict`, `dataclass`, or Pydantic
  `BaseModel`; every state key has an independent reducer (default: overwrite; custom via
  `Annotated[type, reducer_fn]`, e.g. `operator.add` for accumulation). A prebuilt
  `add_messages` reducer (used by `MessagesState`) tracks message IDs so a resumed/edited
  message updates in place rather than duplicating. Graphs support private/internal state
  channels distinct from input/output schemas.
- **`Command` unifies dynamic control**: a single object combining `update` (state change),
  `goto` (routing, including to nodes in a parent graph via `graph=Command.PARENT` — the
  mechanism underlying multi-agent handoffs), and `resume` (the only valid pattern for
  supplying input after an `interrupt()`). Mixing static edges and `Command`-based dynamic
  routing from the same node is discouraged since both paths execute.
- **Two-tier persistence — checkpointers vs. stores**: **checkpointers**
  (`InMemorySaver`/`MemorySaver`, `SqliteSaver`, `PostgresSaver`, `AsyncPostgresSaver`)
  persist thread-scoped graph-state snapshots for conversation continuity, HITL, time-travel,
  and fault tolerance; **stores** persist app-defined key/value data across threads for
  long-term/cross-thread memory. Checkpoints are written at superstep boundaries (not
  mid-node), so a resumed node re-executes from its start — placing an idempotency burden on
  node authors, similar in spirit to Temporal's determinism requirements (`temporal.md`) but
  scoped at node granularity rather than full-function replay.
- **Human-in-the-loop via `interrupt()`**: calling `interrupt(payload)` inside a node pauses
  the run, checkpoints state, and surfaces the payload; resuming requires
  `Command(resume=value)` against the same `thread_id`, and the *entire node re-runs from the
  top* (not from the exact interrupt call site) — with documented rules against wrapping
  `interrupt()` in bare try/except or looping it inside `while True` (causes exponential
  re-execution on resume). Static `interrupt_before`/`interrupt_after` breakpoints exist for
  debugging only, not production HITL.
- **Multi-agent patterns are a documented decision framework, not one mechanism**: four named
  patterns — **Subagents** (main agent calls subagents as tools; strongest isolation/
  parallelism), **Handoffs** (state-triggered dynamic control transfer via
  `Command(goto=..., graph=Command.PARENT)`; best for direct multi-turn user interaction but
  sequential-only), **Skills** (on-demand context loading, single agent stays in control), and
  **Router** (a classification step dispatches to specialized agents). Docs include a
  quantified cost/performance comparison across these patterns, showing no universally "best"
  choice.
- **MCP support is first-party** via a dedicated LangChain-maintained package,
  `langchain-mcp-adapters`, converting MCP tools (stdio, HTTP, streamable-HTTP) into
  LangChain-compatible tools, with a `MultiServerMCPClient` for connecting to several servers
  at once and configurable tool-error handling. Documented caveat: MCP's stdio transport is
  flagged as poorly suited to a web-server deployment context — echoing a similar caveat in
  Google ADK's docs (`google-adk.md`).
- **No first-party A2A protocol support**: unlike Google ADK's bidirectional A2A server/client
  components (`google-adk.md`, `a2a-protocol.md`), no A2A package exists under the
  `langchain-ai` GitHub org and no A2A page appears in current docs. LangGraph's cross-agent
  story is built entirely on its own primitives (subgraphs, parent-graph handoffs,
  `RemoteGraph` for calling a deployed graph as if local) rather than an interoperability
  protocol with other frameworks' agents — a material gap for CF's interest in cross-framework
  agent interop.
- **Deployment is commercial-first via "LangSmith Deployment"**: a framework-agnostic Agent
  Server (also supports Google ADK, Claude Agent SDK, Strands, CrewAI, AutoGen via wrapper
  packages) offering four topologies — fully-managed Cloud, Hybrid (LangChain-hosted control
  plane + self-hosted data plane), self-hosted-with-control-plane (your own Kubernetes), and a
  no-control-plane Standalone Agent Server (Docker/Compose/Kubernetes, bring-your-own
  Postgres/Redis). All four share the same Agent Server runtime and execution model
  (assistants/threads/runs); persistence is handled automatically by the server.
- **Observability is LangSmith-centric, not OTel-GenAI-convention-centric**: tracing is opt-in
  via API key, integrated with dashboards, alerting, and user-feedback collection. This
  contrasts with Google ADK's and Microsoft Agent Framework's explicit adoption of OTel GenAI
  semantic conventions (`opentelemetry-genai.md`) — LangSmith's tracing schema is proprietary,
  with no first-party OTLP/OTel GenAI-convention export mentioned in docs reviewed.
- **Adoption signals**: `langgraph` repo ~39.4k stars (vs. `langchain` ~144k, `deepagents`
  ~27.6k), `langchain-mcp-adapters` ~3.6k stars; cited users include Klarna, Uber, J.P.
  Morgan, Replit, and Elastic — one of the most widely adopted agent-orchestration frameworks
  in this survey.

## CF relevance

LangGraph's Pregel-style superstep model and its explicit, quantified comparison of
multi-agent patterns (subagents vs. handoffs vs. skills vs. router) is a useful reference for
CF when reasoning about tradeoffs between isolation, parallelism, and cost in a multi-agent
design — independent of whether CF ever adopts LangGraph itself. Its checkpoint-at-superstep-
boundary durability model is a lighter-weight alternative to Temporal's full-replay or Dapr's
actor-based durability, worth comparing directly. Most notably for CF's stated interest in
cross-framework agent interoperability: LangGraph's total absence of A2A support, despite deep
investment in every other axis (persistence, streaming, HITL, MCP), suggests A2A adoption is
not yet universal across major agent frameworks — CF should not assume A2A support as a given
when evaluating framework interop options.

## Open questions

- Is LangGraph's per-superstep checkpoint durability sufficient for CF's crash-recovery
  expectations, or does the "resumed node re-executes from the top" behavior create
  correctness risk for non-idempotent nodes in a CF-hosted agent runtime?
- Given no first-party A2A support, would CF need to build/sponsor a LangGraph-to-A2A bridge
  if it wanted LangGraph-built agents to interoperate with A2A-native agents (e.g. from Google
  ADK or kagent)?
- LangSmith Deployment's "Standalone Agent Server" (no control plane, bring-your-own Postgres/
  Redis) is the closest thing to a CF-friendly self-hosted deployment target among the options
  surveyed — is this a viable buildpack/service-binding target, or does it assume too much
  Kubernetes-specific tooling?
- How would LangGraph's checkpointer/store split (thread-scoped vs. cross-thread) map onto a
  CF service-binding model, if a platform wanted to offer "LangGraph checkpoint store" as a
  bindable service?
