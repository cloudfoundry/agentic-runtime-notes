---
title: "Google Agent Development Kit (ADK) for Go — Graph-Based Agent Runtime"
author: Ruben Koster (@rkoster)
date: 2026-08-10
tags: [orchestration, inter-agent-comms, observability-governance, runtime-lifecycle, ecosystem-survey]
cf_areas: []
status: draft
sources:
  - https://github.com/google/adk-go
  - https://google.github.io/adk-docs/
  - https://google.github.io/adk-docs/get-started/go/
  - https://google.github.io/adk-docs/2.0/
  - https://google.github.io/adk-docs/a2a/intro/
  - https://google.github.io/adk-docs/deploy/agent-runtime/deploy/
  - https://google.github.io/adk-docs/tools-custom/mcp-tools/
  - https://google.github.io/adk-docs/observability/traces/
  - https://google.github.io/adk-docs/workflows/collaboration/
  - https://google.github.io/adk-docs/agents/workflow-agents/
  - https://google.github.io/adk-docs/agents/models/
---

## Summary

Agent Development Kit (ADK) for Go (`google/adk-go`) is Google's Apache-2.0, code-first
framework for building, evaluating, and deploying AI agents — a parallel, API-compatible
sibling to the original Python ADK (alongside Java, Kotlin, and TypeScript ports), developed
in lockstep with matching version numbers. ADK 2.0 (Go GA'd June 30, 2026, Python GA'd May 19,
2026) replaced the original hierarchical agent-executor model with a **graph-based Workflow
Runtime**, where agents, tools, and functions execute as nodes in an explicit workflow graph.
It is optimized for but not locked to Gemini, ships native MCP and A2A support, deep
OpenTelemetry GenAI-convention tracing, and one-command deployment to Google Cloud's Agent
Runtime (Vertex AI Agent Engine), Cloud Run, or GKE. Notably, kagent's Go engine (see
`kagent.md` in this research set) is built directly on ADK Go, making ADK Go a concrete
substrate choice already adopted by another CNCF-adjacent project surveyed here.

## Key findings

- **Governance, license, maturity**: Apache-2.0, maintained by Google under the `google`
  GitHub org. Module path `google.golang.org/adk/v2` (Go 1.25+). ADK 2.0 is GA as of June 30,
  2026 for Go (Python GA'd ~6 weeks earlier), introducing graph-based workflows, parallel/loop
  execution primitives, and human-in-the-loop tool confirmation as stable features — not
  labeled alpha/preview.
- **Go and Python are lockstep siblings, not a lagging port**: both hit ADK 2.0 GA within
  weeks of each other and ship the *same* breaking changes together (`BaseAgent`→`BaseNode`,
  new `session.Event` fields, `session.NewEvent` requiring `context.Context` as first arg,
  module path bump to `/v2`). Python retains a slightly larger catalog of pre-built
  tools/integrations and some docs show Python-first examples with Go as a secondary tab, but
  core API surface and release cadence are tightly synchronized — a different maturity
  posture than, e.g., MAF's public-preview Go binding (see `microsoft-agent-framework.md`).
- **Graph-based Workflow Runtime (2.0's central change)**: `BaseAgent` now subclasses
  `BaseNode`; agents, tools, and functions are evaluated as nodes in a Workflow Graph rather
  than as standalone recursive executors. Legacy method overrides (`_run_async_impl`, custom
  `Run`) are bypassed by the graph engine — custom logic must move into
  `BeforeAgentCallback`/`AfterAgentCallback` hooks. This is architecturally close to
  Microsoft Agent Framework's `executors`/`edges` workflow graph model, suggesting explicit
  workflow-graph orchestration (vs. purely LLM-improvised control flow) is converging as an
  industry default among major agent SDKs.
- **Two complementary orchestration layers**: (1) **template workflow agents**
  (Sequential/Loop/Parallel) — deterministic control-flow agents that don't consult an LLM to
  decide what runs next, now marked "superseded" by graph workflows in 2.0 but still
  supported; and (2) **collaborative workflows**, where a coordinator `LlmAgent` delegates to
  declared `SubAgents`, each auto-exposed to the coordinator as a callable tool. Three
  delegation modes govern control-flow return semantics: `chat` (manual
  `transfer_to_agent` handback), `task` (auto-return via `finish_task`, can ask clarifying
  questions), and `single_turn` (no user interaction, supports parallel execution). Task-mode
  agents must be leaves and run in an isolated session branch, invisible to sibling agents
  until the parent collects results — a more structured isolation model than a shared
  pub/sub topic (contrast with Dapr Agents' broadcast-based orchestration, `dapr-agents.md`).
- **Sessions/state as first-class, source-controllable concerns**: the runtime is built
  around a `session.Service`/`Event` log, with documented support for "rewinding" and
  "migrating" sessions, and layered context management (filtering irrelevant events,
  summarizing old turns, lazy-loading artifacts, token tracking) rather than naive prompt
  concatenation. Custom `session.Service` implementations backed by SQL/NoSQL must account
  for the new 2.0 Event fields (`NodeInfo`, `Routes`, `RequestedInput`, `Output`,
  `IsolationScope`) unless storing events as opaque JSON blobs.
- **Tool integration incl. MCP as both client and server**: a `tool.Tool` interface covers
  function tools (`functiontool.New`), built-in tools (Google Search, Maps grounding via
  `geminitool`), OpenAPI-derived tools, and MCP via `McpToolset` — ADK can *consume* external
  MCP servers (stdio/SSE/streamable-HTTP) and *expose* ADK tools as an MCP server itself. Docs
  explicitly call out MCP connection lifecycle/statefulness (session affinity, connection
  cleanup, re-initialization after process restore) as an operational concern for scaled
  deployments — a smaller-scope but analogous concern to Dapr Agents' child-workflow-per-MCP-
  call durability guarantee.
- **First-class, bidirectional A2A support**: an `A2AServer` component exposes any ADK agent
  as a network-accessible A2A service (see `a2a-protocol.md`), and `RemoteA2aAgent` consumes a
  remote A2A-exposed agent as if it were a local sub-agent/tool, abstracting transport, auth,
  and serialization. ADK's A2A layer preserves reasoning/thought traces, tracks long-running
  tool calls across the network boundary, and passes file artifacts between agents. Docs
  frame A2A vs. local sub-agents as an explicit tradeoff: network/cross-team/cross-language
  boundaries → A2A; in-process modules → local sub-agents.
- **Deployment is "anywhere," with no built-in durable-execution substrate of its own**:
  self-host on arbitrary infra, or one-command deploy (`adkgo deploy agentengine`) to Google
  Cloud's Agent Runtime (Vertex AI Agent Engine), with Cloud Run and GKE also documented as
  first-class targets (including a sidecar-MCP-server pattern for GKE). No mention of Dapr or
  Temporal integration; the closest thing to a durability story is a `platform` package
  providing pluggable time/UUID providers for "deterministic, replay-safe events," aimed at
  external workflow engines rather than a built-in durable-execution guarantee. This mirrors
  the pattern seen in Temporal's and MAF's notes: ADK treats durable execution as a substrate
  to plug in, not a feature it ships. **kagent's Go engine is built directly on top of ADK
  Go**, with kagent's own Kubernetes CRD/controller layer supplying the durability/scheduling
  ADK itself doesn't provide (see `kagent.md`) — a concrete example of another project in this
  research set choosing ADK Go as its agent-execution substrate.
- **Deep OpenTelemetry GenAI semantic-convention support**: implements OTel GenAI spans
  (`invoke_agent`, `invoke_workflow`, `execute_tool`, `generate_content`) with attributes like
  `gen_ai.operation.name`, `gen_ai.agent.name`, `gen_ai.usage.input_tokens` (see
  `opentelemetry-genai.md`), emitting standard OTLP compatible with Jaeger, Grafana Tempo,
  Datadog, and Cloud Trace, and propagating trace context across process boundaries so a tool
  calling an external service links back to the agent's root trace.
- **Not Gemini-locked**: dedicated docs exist for Gemini, Gemma, Claude, OpenAI, Ollama, vLLM,
  LiteLLM (multi-provider proxy), LiteRT-LM (on-device), Apigee AI Gateway, and Vertex-hosted
  models, plus a "model routing" feature for dynamic model selection — though the Go
  quickstart's own example wires up `gemini.NewModel` directly, reflecting first-party Gemini
  SDK integration as the default path.

## CF relevance

ADK Go is a second, independent data point (after kagent, MAF, and Dapr Agents) that
graph/workflow-based orchestration with explicit sub-agent delegation modes is becoming the
standard shape for production agent frameworks — useful context regardless of whether CF ever
runs ADK-based agents directly. Its A2A-vs-local-sub-agent framing ("network boundary → A2A,
in-process → sub-agent") is a clean mental model CF could reuse when deciding where an
"agent" workload boundary should sit relative to CF's existing app/process boundary. That
kagent already builds its Go runtime on ADK Go also means any CF investigation of kagent
(flagged as a template for a "CF operator agent" in `kagent.md`) is implicitly an
investigation of ADK Go's architecture one layer down — worth keeping in mind so the two
notes aren't treated as fully independent options.

## Open questions

- ADK's `platform` package exposes deterministic time/UUID providers "for replay-safe
  events" but ships no workflow-replay engine itself — would a CF-native agent runtime want
  to pair ADK-style agent definitions with a separate durable-execution substrate (Temporal,
  Dapr Workflows, or something CF-native), the same way kagent pairs it with Kubernetes CRDs?
- The `task`/`single_turn`/`chat` sub-agent isolation model (isolated session branches,
  invisible to siblings until results are collected) is a stronger isolation default than
  Dapr Agents' shared pub/sub topic — is this difference significant enough to matter for a
  CF multi-agent trust/isolation model, or a superficial API difference over similar
  underlying guarantees?
- How would ADK's MCP connection-affinity concerns (session affinity, cleanup on restart)
  interact with CF's own instance placement/rebalancing, if ADK agents ran as CF app
  instances?
- Given ADK Go and Python are kept in lockstep, is there a reason to standardize on the Go
  implementation specifically for a CF-adjacent use case (e.g. matching CF's own Go-heavy
  codebase, cf. kagent's Go-vs-Python cold-start tradeoff in `kagent.md`), or does the choice
  come down purely to the language of the surrounding platform code?
