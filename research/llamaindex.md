---
title: "LlamaIndex Workflows & AgentWorkflow — Event-Driven, Graph-Free Orchestration"
author: Ruben Koster (@rkoster)
date: 2026-08-10
tags: [orchestration, inter-agent-comms, observability-governance, ecosystem-survey]
cf_areas: []
status: draft
sources:
  - https://github.com/run-llama/llama_index
  - https://github.com/run-llama/llama-agents
  - https://github.com/run-llama/llama-agents/blob/main/packages/llama-index-workflows/README.md
  - https://github.com/run-llama/llama_index/blob/main/docs/src/content/docs/framework/understanding/agent/multi_agent.md
  - https://github.com/run-llama/llama_index/blob/main/docs/src/content/docs/framework/understanding/agent/state.md
  - https://github.com/run-llama/llama_index/blob/main/docs/src/content/docs/framework/understanding/agent/human_in_the_loop.md
  - https://github.com/run-llama/llama_index/blob/main/docs/src/content/docs/framework/module_guides/mcp/index.md
  - https://github.com/run-llama/llama_index/blob/main/docs/src/content/docs/framework/module_guides/observability/index.md
  - https://github.com/run-llama/llama_deploy/blob/main/README.md
  - https://llamatrace.com/
---

## Summary

LlamaIndex began in 2022 as "GPT Index," a RAG/data framework for connecting LLMs to private
data (connectors, indices, retrievers, query engines) — a positioning still visible in its
MIT-licensed core (~51.5k GitHub stars, maintained by the venture-backed startup LlamaIndex,
Inc.). Over 2024–2026 the project extracted its multi-step orchestration primitives into a
standalone, event-driven engine — now published as its own package, **`llama-index-workflows`**
— which underpins **`AgentWorkflow`**, LlamaIndex's built-in multi-agent orchestration
abstraction. Architecturally, LlamaIndex Workflows takes the opposite design bet from
LangGraph (`langgraph.md`): instead of an explicit `StateGraph` of nodes/edges, a `Workflow`
is just a bag of `@step`-decorated async methods that declare, via Python type hints, which
typed `Event` subclasses they consume and emit — the runtime infers the implicit graph and
validates it, rather than requiring the developer to wire it explicitly. Deployment has moved
from the now-deprecated `llama_deploy` to a newer `llama-agents` toolchain
(`llama-agents-server`/`client`/`llamactl`), alongside LlamaIndex Inc.'s commercial LlamaCloud
platform. No official A2A protocol package exists.

## Key findings

- **Origin and evolution**: LlamaIndex started as a "data framework" for RAG and is
  MIT-licensed; the GitHub README now brands the repo "the leading document agent and OCR
  platform," reflecting a pivot toward document-agent/OCR use cases (LlamaParse) alongside its
  original RAG roots. Governed by LlamaIndex, Inc. (~51.5k stars, 7.9k forks).
- **Workflows engine extracted into its own package**: `llama_index.core.workflow` is now a
  thin re-export shim over a standalone MIT package, `llama-index-workflows` (import name
  `workflows`), developed in a separate monorepo `run-llama/llama-agents` — decoupling the
  orchestration engine from the RAG framework and making it independently reusable.
- **Event-driven, no explicit graph**: a `Workflow` subclass declares `@step`-decorated async
  methods; each step's Python type hints (parameter type = accepted `Event` subclass, return
  type = emitted `Event` subclass(es)) implicitly define the control-flow graph. There is no
  `add_edge`/`add_node` API as in LangGraph's `StateGraph` — the framework statically
  validates the *inferred* graph at construction time (reachability, terminal-event, dead-end
  checks, individually skippable per step). Loops, branches, and fan-out/fan-in are expressed
  simply by steps that emit multiple event types or by cycles in the event/step type graph.
- **Concurrency is per-step, not a separate primitive**: each `@step` has a `num_workers`
  parameter (default 4) controlling how many concurrent instances of that step can process
  events from its input queue simultaneously — parallelism is declared locally on the step
  rather than via a graph-level fan-out API like LangGraph's `Send`.
- **`AgentWorkflow` — built-in multi-agent orchestration on top of Workflows**: a
  pre-configured `Workflow` accepting a list of agents (`FunctionAgent`, `ReActAgent`,
  `CodeActAgent`), a root agent, and per-agent `can_handoff_to` lists; the currently active
  agent can autonomously hand off control to a named peer or return control to the user.
  LlamaIndex's docs frame this as one of three explicit multi-agent patterns — (1)
  `AgentWorkflow` handoff/"swarm," (2) an orchestrator agent with sub-agents exposed as
  callable tools, (3) a fully custom DIY planner workflow — with an explicit trade-off table,
  directly comparable to LangGraph's four named multi-agent patterns
  (Subagents/Handoffs/Skills/Router, `langgraph.md`).
- **State via `Context`, typed and serializable**: a `Context[StateModel]` object (optionally
  parameterized with a Pydantic state model) persists across `.run()` calls with the same
  `ctx`, enabling multi-turn memory; state is mutated via `async with ctx.store.edit_state()`.
  Contexts are explicitly serializable (`ctx.to_dict()` / `Context.from_dict()`), so workflow
  state can be persisted to a DB/file and reloaded later — a lighter-weight analog to
  LangGraph's checkpointer-backed thread state.
- **Step-level checkpointing via `WorkflowCheckpointer`**: a separate wrapper records a
  checkpoint at the completion of each step (input event, output event, and a context-state
  snapshot), viewable/filterable by step name or event type, and resumable from any specific
  checkpoint (creating a new run ID). Individual steps can be excluded from checkpointing —
  closer to LangGraph's superstep-boundary checkpointing than to full mid-node replay.
- **Human-in-the-loop via `InputRequiredEvent`/`HumanResponseEvent`**: a step calls
  `ctx.wait_for_event(HumanResponseEvent, ...)`, emitting a `waiter_event` on the stream and
  suspending until a matching response event arrives. Docs explicitly note that for long
  waits, the `Context` should be serialized and persisted so the run can resume later — tying
  HITL directly to the state-serialization mechanism rather than a dedicated `interrupt()`
  primitive as in LangGraph.
- **MCP support is first-party but consumer-only in core**: `llama-index-tools-mcp` provides
  `BasicMCPClient`/`McpToolSpec` to convert an MCP server's tools into LlamaIndex tool objects,
  supporting SSE, streamable-HTTP, and local-process transports (`mcp-protocol.md`). Separate
  guides cover serving LlamaIndex workflows as MCP servers.
- **No first-party A2A protocol support found**: no A2A-named package or repo exists under
  `run-llama`, and no A2A page appears in the docs tree — the same gap identified for
  LangGraph (`langgraph.md`), in contrast to Google ADK's bidirectional A2A support
  (`google-adk.md`). Cross-agent interop is built entirely on `AgentWorkflow` handoffs,
  agents-as-tools, or the `llama-agents-client`/`llama-agents-server` REST wrapper for calling
  a deployed workflow remotely.
- **Deployment has moved from `llama_deploy` (deprecated) to the `llama-agents` toolchain**:
  the standalone `llama_deploy` repo is explicitly marked deprecated, redirecting to
  `llama-agents`. The current self-hosted path is layered: use `llama-index-workflows` as a
  plain library; wrap it with `llama-agents-server`'s `WorkflowServer` to expose it as a REST
  API (streaming, persistence, HITL) inside an existing Starlette/FastAPI app; or use
  `llamactl`, a CLI, to scaffold/deploy to LlamaCloud, AWS Bedrock AgentCore (via a dedicated
  `llama-agents-agentcore` package, `aws-agents.md`), or custom infrastructure. Notably, the
  main LlamaIndex docs' own "Deployment" page is an unfinished stub — the substantive
  deployment story lives in the separate `llama-agents` monorepo docs.
- **Observability: OpenTelemetry is first-party, LlamaTrace is a commercial partnership**:
  `llama-index-observability-otel` gives an instrumentor that traces LlamaIndex activity in
  OTel span format, exportable to any OTLP backend. Separately, **LlamaTrace** is LlamaIndex
  Inc.'s partnership with Arize, built on the open-source Arize Phoenix project, offering a
  hosted tracing/eval platform — Phoenix can alternatively be run fully self-hosted with no
  LlamaTrace account.
- **Adoption signals**: 51.5k stars on the core `llama_index` repo (vs. `llama-agents`'s 437
  stars, reflecting how new the standalone Workflows/AgentWorkflow split is); the
  now-deprecated `llama_deploy` repo separately accrued 2,067 stars, indicating meaningful
  prior interest in the deployment story even before its replacement.

## CF relevance

LlamaIndex's event-driven "no explicit graph, just typed events" design is a genuinely
different point in the orchestration-framework design space than LangGraph's, Google ADK's, or
Microsoft Agent Framework's explicit graph models — worth comparing directly if CF wants to
evaluate the tradeoff between explicit, statically-inspectable control flow (easier to reason
about/validate ahead of time) versus implicit, type-inferred control flow (less boilerplate,
but the "graph" only exists as a derived property of the code). Its checkpoint-plus-serializable-
context model is a lighter-weight durability mechanism than Temporal's full replay
(`temporal.md`) or Dapr's actor/state-store model, similar in spirit to CrewAI's file/SQLite
checkpointing (`crewai.md`) — another data point for a CF-native durable-execution story that
doesn't require standing up a separate service. The unfinished "Deployment" stub in the main
docs, alongside a still-immature separate deployment toolchain, is also a useful signal that
not every framework in this ecosystem has a mature, first-party hosting story — CF should
expect to fill that gap itself for some frameworks rather than assuming vendor tooling will
always be production-ready.

## Open questions

- Is LlamaIndex's implicit, type-inferred workflow graph a net positive or negative for a
  CF-hosted agent platform that might want to statically validate/audit an agent's possible
  execution paths before deployment — does the lack of an explicit graph definition make this
  meaningfully harder than with LangGraph or Google ADK?
- Given the immaturity of LlamaIndex's own deployment tooling (`llama_deploy` deprecated,
  `llama-agents` still young, main docs' deployment page a stub), would a CF buildpack for
  LlamaIndex workflows need to do more platform-specific work than for a more deployment-mature
  framework like LangGraph or Google ADK?
- LlamaIndex's `Context` serialization for HITL/long-running pauses relies on the application
  choosing where to persist it — is this a good candidate for a CF-native "workflow context"
  bindable service, similar to the checkpoint-store question raised in `langgraph.md`?
- With no first-party A2A support (matching the gap already flagged for LangGraph), does this
  reinforce that CF should not assume A2A as a universal baseline across the ecosystem when
  planning cross-framework interoperability?
