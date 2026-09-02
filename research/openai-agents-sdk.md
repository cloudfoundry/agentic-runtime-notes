---
title: "OpenAI Agents SDK — Minimal Primitives, Provider-Agnostic Agent Loop"
author: Ruben Koster (@rkoster)
date: 2026-08-10
tags: [orchestration, inter-agent-comms, observability-governance, ecosystem-survey]
cf_areas: []
status: draft
sources:
  - https://github.com/openai/openai-agents-python
  - https://openai.github.io/openai-agents-python/
  - https://openai.github.io/openai-agents-python/agents/
  - https://openai.github.io/openai-agents-python/tools/
  - https://openai.github.io/openai-agents-python/guardrails/
  - https://openai.github.io/openai-agents-python/handoffs/
  - https://openai.github.io/openai-agents-python/multi_agent/
  - https://openai.github.io/openai-agents-python/sessions/
  - https://openai.github.io/openai-agents-python/mcp/
  - https://openai.github.io/openai-agents-python/tracing/
  - https://openai.github.io/openai-agents-python/models/
  - https://github.com/openai/openai-agents-js
  - https://github.com/openai/swarm
ratings:
  platform-impact:
    value: 66
    note: 'Initial review of OpenAI Agents SDK — Minimal Primitives, Provider-Agnostic Agent Loop: its subject and tags indicate how broadly the capability could affect an agentic platform.'
  maturity:
    value: 76
    note: 'Initial review of OpenAI Agents SDK — Minimal Primitives, Provider-Agnostic Agent Loop: this score reflects the amount of established external practice visible in the note.'
  novelty:
    value: 62
    note: 'Initial review of OpenAI Agents SDK — Minimal Primitives, Provider-Agnostic Agent Loop: this score reflects how distinct or emerging the approach appears in the current landscape.'
  actionability:
    value: 58
    note: 'Initial review of OpenAI Agents SDK — Minimal Primitives, Provider-Agnostic Agent Loop: this score reflects how readily the material could guide a focused experiment or follow-up.'

---

## Summary

The OpenAI Agents SDK (`openai-agents-python`, MIT-licensed) is a lightweight,
provider-agnostic Python framework for building multi-agent workflows — explicitly a
"production-ready upgrade" of OpenAI's earlier experimental **Swarm** project. Its
architecture centers on a small primitive set: `Agent` (LLM + instructions + tools +
guardrails + handoffs), `Runner` (executes the agent loop), `handoffs` and `agents-as-tools`
(two complementary multi-agent orchestration patterns), and `guardrails` (input/output
validation). It ships built-in `Sessions` for conversation-history persistence (SQLite by
default, with pluggable Redis/SQLAlchemy/MongoDB/Dapr/encrypted backends) and built-in
`Tracing` integrated with OpenAI's hosted dashboard, plus an extensive third-party
observability ecosystem. It has no built-in durable-execution engine of its own — that gap is
explicitly filled by separate integrations from Temporal and Dapr Agents (both covered
elsewhere in this research set).

## Key findings

- **Origin, license, governance, Swarm lineage**: MIT-licensed, maintained directly under the
  `openai` GitHub org. Docs explicitly state it is "a production-ready upgrade of our previous
  experimentation for agents, Swarm" — Swarm remains available but is framed as an
  educational/experimental predecessor, superseded by this SDK. A first-party JS/TS sibling
  (`openai-agents-js`) also exists.
- **Adoption signal**: ~28.5k GitHub stars, ~4.5k forks, 2,040+ commits on `main` — a large,
  active repo with a dedicated TypeScript sibling, indicating broad usage beyond OpenAI's own
  docs/examples.
- **Deliberately minimal core primitives**: `Agent` (LLM + instructions + tools + guardrails +
  handoffs), `Runner` (runs the agent loop via `run`/`run_sync`/`run_streamed`), `RunConfig`
  for per-run overrides, and `Sessions` for memory — stated design principles are "enough
  features to be worth using, but few enough primitives to make it quick to learn" and "works
  great out of the box, but customizable."
- **Two named, complementary multi-agent patterns**: **handoffs** transfer full control of the
  conversation to a specialist agent, which becomes the active agent for the rest of the turn
  (best when a specialist should own user interaction directly). **Agents-as-tools**
  (`Agent.as_tool()`) keep a manager agent in control, calling specialist agents as callable
  tools and synthesizing outputs (best when a manager must own the final answer or combine
  multiple specialists' outputs under one guardrail surface). The two can be combined — a
  handoff target can itself call other agents as tools for narrow subtasks.
- **Tools span function tools, hosted tools, and MCP**: any Python function becomes a tool via
  automatic schema generation; hosted tools (web search, file search, code interpreter,
  computer use) run inside OpenAI's Responses API infrastructure; MCP servers are supported
  via four transports — hosted `HostedMCPTool` (server-side), `MCPServerStreamableHttp`,
  deprecated `MCPServerSse`, and local-process `MCPServerStdio` — with tool filtering, prompt
  retrieval, caching, and approval-policy gating for sensitive MCP tool calls.
- **Sessions provide client-managed conversation memory, not a durable-execution substrate**:
  `Session` objects (`SQLiteSession` default; extensions for `RedisSession`,
  `SQLAlchemySession`, `MongoDBSession`, `DaprSession`, `OpenAIConversationsSession`,
  `EncryptedSession`) automatically retrieve/persist history around a run. Interrupted/paused
  runs (e.g. pending human approval) can be resumed via `result.to_state()` →
  `state.approve(...)` → re-run against the same session — turn-level resumption, not
  workflow-engine-style replay/crash recovery.
- **A first-party-documented `DaprSession`**: the SDK docs list `DaprSession` (via Dapr
  state-store sidecars, 30+ backends, TTL/consistency controls) as a built-in session
  implementation, confirming the Dapr↔OpenAI-Agents-SDK integration referenced in
  `dapr-agents.md` is real and maintained — though it addresses session/memory storage
  specifically, not full agent-execution durability.
- **Built-in tracing, no native OTel export**: tracing is enabled by default, capturing
  `agent_span`, `generation_span`, `function_span`, `guardrail_span`, `handoff_span`, viewable
  in OpenAI's hosted Traces dashboard. 25+ third-party "ecosystem integrations" (Datadog,
  Langfuse, MLflow, Arize-Phoenix, W&B Weave, etc.) consume the tracing API surface via each
  vendor's own instrumentation — not a standardized OTel exporter shipped by OpenAI itself,
  unlike Google ADK's native OTel GenAI convention support (`google-adk.md`,
  `opentelemetry-genai.md`). Tracing is unavailable for orgs under Zero Data Retention.
- **No native A2A protocol support found**: neither the README, docs navigation, nor the
  multi-agent/MCP pages reference the Agent2Agent protocol; multi-agent coordination is scoped
  to in-process handoffs/agents-as-tools (plus an experimental OpenAI-hosted multi-agent beta)
  rather than a standardized cross-process wire protocol like A2A — contrast with Google ADK's
  first-party bidirectional A2A support (`google-adk.md`).
- **No durable-execution engine; "bring your own infrastructure" deployment**: the SDK is a
  library, not a hosted runtime/platform (unlike LangGraph Platform or Vertex Agent Engine) —
  no bundled server, scheduler, or workflow-replay engine. This is consistent with why
  dedicated durable-execution integrations exist as separate projects: Temporal's and Dapr
  Agents' official integrations with this SDK exist precisely to backfill this gap
  (`temporal.md`, `dapr-agents.md`).
- **Low provider lock-in by design**: default models are OpenAI's, on either the Responses API
  (recommended) or Chat Completions API, but the SDK advertises "100+ other LLMs" support
  through a custom `ModelProvider` per run, per-agent model overrides (mixing
  providers/models within one workflow), and two first-party third-party adapters — Any-LLM
  and LiteLLM — plus a `MultiProvider` for prefix-based model routing.
- **Guardrails and HITL are first-class, run-parallel constructs**: input/output guardrails
  run in parallel with agent execution and can fail fast before wasting further LLM calls; a
  dedicated human-in-the-loop mechanism supports interruption/approval flows with resumable
  run state. An experimental "hosted multi-agent" mode lets a root agent create and coordinate
  server-hosted subagents while local function tools still execute client-side — explicitly
  incompatible with SDK handoffs.

## CF relevance

The OpenAI Agents SDK's minimal-primitives philosophy (a handful of composable concepts vs. a
full graph engine) is a useful contrast point to the heavier frameworks in this survey
(LangGraph, Microsoft Agent Framework, Google ADK) — it demonstrates that a lightweight,
library-only agent SDK with no bundled hosting/durability layer is a viable, widely-adopted
design point, not just a stepping stone toward a full platform. Its complete reliance on
external durable-execution integrations (Temporal, Dapr Agents) rather than shipping its own
is a clean illustration of the "agent framework vs. durability substrate" separation of
concerns CF should expect to make explicit in its own agent runtime story. The `DaprSession`
integration is also a concrete existing bridge CF could point to if evaluating Dapr as a
session/state substrate independent of which agent framework produced the workload.

## Open questions

- Given the SDK ships no hosting/runtime layer at all, would a CF-native "agent buildpack"
  for this SDK look meaningfully different from a generic Python buildpack — i.e. is there
  anything platform-specific to add, or does it just need process supervision plus a bound
  session-store service?
- Is the SDK's reliance on external durability integrations (Temporal, Dapr) a pattern CF
  should standardize on — i.e. should CF's own agent runtime treat "durable execution" as a
  pluggable, bindable capability rather than a framework-level feature?
- How significant is the lack of native A2A support for CF's cross-framework interoperability
  goals, given this is one of the most widely-adopted agent SDKs surveyed?
- The experimental "hosted multi-agent" mode moves orchestration server-side into OpenAI's own
  infrastructure — does this signal a broader industry shift toward vendor-hosted
  orchestration that CF should watch for parallels to Vertex Agent Engine or Azure Foundry?
