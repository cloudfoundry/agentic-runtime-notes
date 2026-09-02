---
title: "Google Agent Development Kit (ADK) — Graph-Based, Multi-Language Agent Framework"
author: Ruben Koster (@rkoster)
date: 2026-08-10
tags: [orchestration, inter-agent-comms, observability-governance, runtime-lifecycle, ecosystem-survey]
cf_areas: []
status: draft
sources:
  - https://github.com/google/adk-python
  - https://github.com/google/adk-go
  - https://google.github.io/adk-docs/
  - https://google.github.io/adk-docs/2.0/
  - https://google.github.io/adk-docs/get-started/about/
  - https://google.github.io/adk-docs/a2a/intro/
  - https://google.github.io/adk-docs/deploy/agent-runtime/deploy/
  - https://google.github.io/adk-docs/tools-custom/mcp-tools/
  - https://google.github.io/adk-docs/observability/traces/
  - https://google.github.io/adk-docs/workflows/collaboration/
  - https://google.github.io/adk-docs/agents/workflow-agents/
  - https://google.github.io/adk-docs/agents/models/
  - https://google.github.io/adk-docs/evaluate/
ratings:
  platform-impact:
    value: 78
    note: 'Initial review of Google Agent Development Kit (ADK) — Graph-Based, Multi-Language Agent Framework: its subject and tags indicate how broadly the capability could affect an agentic platform.'
  maturity:
    value: 76
    note: 'Initial review of Google Agent Development Kit (ADK) — Graph-Based, Multi-Language Agent Framework: this score reflects the amount of established external practice visible in the note.'
  novelty:
    value: 62
    note: 'Initial review of Google Agent Development Kit (ADK) — Graph-Based, Multi-Language Agent Framework: this score reflects how distinct or emerging the approach appears in the current landscape.'
  actionability:
    value: 66
    note: 'Initial review of Google Agent Development Kit (ADK) — Graph-Based, Multi-Language Agent Framework: this score reflects how readily the material could guide a focused experiment or follow-up.'

---

## Summary

Google's Agent Development Kit (ADK) is an Apache-2.0, code-first framework for building,
evaluating, and deploying AI agents — originally built internally at Google to power agentic
products (Agentspace and other Gemini-powered agent surfaces) before being open-sourced, and
now maintained as a family of first-party, API-compatible implementations (Python — flagship,
Go, Java, Kotlin, TypeScript) kept in lockstep under the `google` GitHub org. ADK 2.0 (Python
GA'd May 19, 2026, other languages following within weeks) replaced the original hierarchical
agent-executor model with a **graph-based Workflow Runtime**, paired with a structured **Task
API** for agent-to-agent delegation. Beyond agent definition, ADK bundles broad tool
integration (function tools, OpenAPI, MCP client+server), first-class bidirectional A2A
protocol support, built-in evaluation tooling (trajectory + response-quality scoring), and
deep OpenTelemetry GenAI-convention observability — with deployment paths from self-hosted
containers to Google Cloud's Agent Runtime, Cloud Run, and GKE.

## Key findings

- **Origin, license, governance**: ADK is Google's own internal agent framework — used for
  products like Agentspace and other Gemini-powered agent surfaces — subsequently open-sourced
  under Apache-2.0. It lives entirely under the `google` GitHub org (`adk-python`, `adk-go`,
  `adk-java`, `adk-kotlin`, `adk-js`, plus `adk-docs`, `adk-web`, and `adk-samples`), not a
  third-party or community-donated project. `adk-python` alone has ~21k GitHub stars and a
  roughly bi-weekly release cadence.
- **Multi-language strategy is first-party and lockstep, not community ports**: Python, Go,
  Java, Kotlin, and TypeScript are all maintained by Google in the same org, share the same
  version numbers, and hit the ADK 2.0 GA milestone within weeks of each other, shipping the
  same breaking API changes together. The docs site presents all languages side-by-side in
  code tabs rather than treating any as secondary — though Python retains the largest catalog
  of pre-built tools/integrations and is generally the "docs-first" language, and some
  deploy/integration guides show Python examples with other languages as secondary tabs. This
  is a notably different maturity posture than, e.g., Microsoft Agent Framework's
  public-preview Go binding (see `microsoft-agent-framework.md`).
- **Core primitives**: an `Agent` (typically an `LlmAgent`, defined by model + instruction +
  tools) and a `Workflow` (orchestrates agents/tasks as a graph), with supporting concepts —
  `Tool`, `Callback`, `Session`/`State`/`Event` (conversation context and history), `Memory`
  (cross-session long-term recall, distinct from session state), `Artifact` (file/binary
  management), code execution, and ReAct-style planning — all coordinated by a `Runner`
  engine.
- **ADK 2.0's central architectural shift is a graph-based Workflow Runtime**: agents, tools,
  and functions now execute as nodes in an explicit `Workflow` graph (edges like
  `("START", agentA, agentB)`) supporting routing, fan-out/fan-in, loops, retries, state
  management, dynamic nodes, human-in-the-loop pauses, and nested workflows — replacing the
  older recursive agent-executor model where control flow was implicit in code (custom logic
  now has to move into `BeforeAgentCallback`/`AfterAgentCallback` hooks rather than method
  overrides). This is paired with a new **Task API** for structured agent-to-agent delegation.
  The shift is architecturally close to Microsoft Agent Framework's `executors`/`edges` graph
  model, suggesting explicit workflow-graph orchestration (vs. purely LLM-improvised control
  flow) is converging as an industry default among major agent SDKs.
- **Two complementary orchestration layers coexist**: (1) **template workflow agents**
  (`SequentialAgent`, `ParallelAgent`, `LoopAgent`) — deterministic control-flow agents that
  don't consult an LLM to decide what runs next, now positioned as "superseded" by graph
  workflows in 2.0 but still supported; and (2) **collaborative workflows**, where a
  coordinator `LlmAgent` delegates to declared sub-agents, each auto-exposed to the
  coordinator as a callable tool (`AgentTool`). Three delegation modes govern control-flow
  return semantics: `chat` (manual `transfer_to_agent` handback, full user interaction),
  `task` (auto-return via `finish_task`, can still ask clarifying questions), and
  `single_turn` (no user interaction, supports parallel execution). Task-mode agents must be
  leaves and run in an isolated session branch, invisible to sibling agents until the parent
  collects results — a more structured isolation model than a shared pub/sub topic (contrast
  with Dapr Agents' broadcast-based orchestration, `dapr-agents.md`).
- **Sessions/state as first-class, source-controllable concerns**: the runtime is built
  around a `Session`/`Event` log, with documented support for "rewinding" and "migrating"
  sessions, and layered context management (filtering irrelevant events, summarizing old
  turns, lazy-loading artifacts, token tracking) rather than naive prompt concatenation.
  Custom session-store implementations backed by SQL/NoSQL must account for new 2.0 Event
  fields (node info, routes, requested input, output, isolation scope) unless storing events
  as opaque JSON blobs.
- **Broad tool integration, including MCP as both client and server**: `FunctionTool` for
  custom functions, `AgentTool` (agents used as tools), built-in tools (Google Search, code
  execution, Maps grounding), OpenAPI-derived tools, and MCP support in both directions — ADK
  agents can consume external MCP servers (stdio/SSE/streamable-HTTP) and be exposed as an MCP
  server themselves. Docs explicitly call out MCP connection lifecycle/statefulness (session
  affinity, connection cleanup, re-initialization after process restore) as an operational
  concern for scaled deployments — a smaller-scope but analogous concern to Dapr Agents'
  child-workflow-per-MCP-call durability guarantee.
- **First-class, bidirectional A2A protocol support**: an A2A server component exposes any
  ADK agent as a network-accessible A2A service (see `a2a-protocol.md`), and a remote-agent
  component consumes a remote A2A-exposed agent as if it were a local sub-agent/tool,
  abstracting transport, auth, and serialization while preserving reasoning/thought traces,
  tracking long-running tool calls across the network boundary, and passing file artifacts
  between agents. Docs frame A2A vs. local sub-agents as an explicit tradeoff:
  network/cross-team/cross-language boundaries → A2A; in-process modules → local sub-agents.
- **Deployment is "anywhere," with no bundled durable-execution engine**: self-host on
  arbitrary infrastructure, or one-command deploy to Google Cloud's Agent Runtime (Vertex AI
  Agent Engine), Cloud Run, or GKE — all inheriting managed infra, auth, Cloud Trace
  observability, and security without code changes. ADK ships no durable-execution/
  crash-recovery substrate of its own; it exposes primitives (deterministic time/UUID
  providers "for replay-safe events") aimed at pairing with an external durability layer
  rather than providing one itself. This mirrors the pattern seen in Temporal's and MAF's
  notes: ADK treats durable execution as a substrate to plug in, not a feature it ships.
- **Adoption signal — kagent builds on ADK**: kagent (a CNCF-adjacent Kubernetes-native agent
  platform, covered separately in `kagent.md`) builds its Go execution engine directly on top
  of ADK, using it as the agent-execution substrate while layering its own Kubernetes
  CRD/controller model on top for scheduling and durability — a concrete example of ADK being
  adopted as infrastructure by another agent-orchestration project, not only used directly by
  end developers.
- **Deep OpenTelemetry GenAI semantic-convention observability**: implements OTel GenAI spans
  (`invoke_agent`, `invoke_workflow`, `execute_tool`, `generate_content`) with attributes like
  `gen_ai.operation.name`, `gen_ai.agent.name`, `gen_ai.usage.input_tokens` (see
  `opentelemetry-genai.md`), emitting standard OTLP compatible with Jaeger, Grafana Tempo,
  Datadog, and Cloud Trace, and propagating trace context across process boundaries so a tool
  calling an external service links back to the agent's root trace.
- **Not Gemini-locked, though Gemini-optimized by default**: dedicated docs/adapters exist for
  Gemini, Gemma, Claude, OpenAI, Ollama, vLLM, LiteLLM (multi-provider proxy), LiteRT-LM
  (on-device), and Apigee AI Gateway, plus a "model routing" feature for dynamic model
  selection at runtime — the model abstraction is the extensibility point, though quickstart
  examples across languages default to a Gemini model out of the box.
- **Built-in evaluation tooling (ADK Eval) is a notable differentiator**: a schema-backed
  evaluation framework distinguishing **trajectory evaluation** (comparing actual vs. expected
  tool-call/step sequences) from **final-response evaluation**, supporting both lightweight
  per-file "unit tests" and larger multi-session "evalsets," a dedicated CLI eval command,
  test-framework integration, a web UI for capturing/editing eval cases with a trace-view
  debugger, and a conformance-test mode that records baseline LLM/tool interactions and
  replays them to catch behavioral drift. Eleven built-in criteria are provided (tool-
  trajectory match, ROUGE-based and LLM-judged response match, rubric-based quality/tool-use
  judging, hallucination/safety scoring, multi-turn task success, etc.), several requiring the
  Vertex Gen AI Evaluation Service API.

## CF relevance

ADK is another independent data point (alongside kagent, Microsoft Agent Framework, and Dapr
Agents) that graph/workflow-based orchestration with explicit sub-agent delegation modes is
converging as the standard shape for production agent frameworks — useful context regardless
of whether CF ever runs ADK-based agents directly. Its A2A-vs-local-sub-agent framing
("network boundary → A2A, in-process → sub-agent") is a clean mental model CF could reuse when
deciding where an "agent" workload boundary should sit relative to CF's existing app/process
boundary. ADK's built-in evaluation/conformance tooling is also a distinctive feature not
mirrored elsewhere in this research set — worth flagging as a separate concern from runtime
orchestration: how would a CF-hosted agent platform support pre-deployment behavioral testing
and drift detection, independent of which orchestration framework produced the agent? Finally,
since kagent already builds its runtime on ADK, any CF investigation of kagent (flagged as a
template for a "CF operator agent" in `kagent.md`) is implicitly an investigation of ADK's
architecture one layer down — worth keeping in mind so the two notes aren't treated as fully
independent options.

## Open questions

- ADK exposes deterministic time/UUID providers "for replay-safe events" but ships no
  workflow-replay engine itself — would a CF-native agent runtime want to pair ADK-style
  agent definitions with a separate durable-execution substrate (Temporal, Dapr Workflows, or
  something CF-native), the same way kagent pairs it with Kubernetes CRDs?
- The `task`/`single_turn`/`chat` sub-agent isolation model (isolated session branches,
  invisible to siblings until results are collected) is a stronger isolation default than Dapr
  Agents' shared pub/sub topic — is this difference significant enough to matter for a CF
  multi-agent trust/isolation model, or a superficial API difference over similar underlying
  guarantees?
- How would ADK's MCP connection-affinity concerns (session affinity, cleanup on restart)
  interact with CF's own instance placement/rebalancing, if ADK agents ran as CF app
  instances?
- Is ADK's built-in evaluation/conformance-testing model (trajectory + response-quality
  scoring, replay-based drift detection) something a CF agent platform should surface as a
  platform-level capability (akin to a CI gate), or is that squarely an application-level
  concern regardless of which framework produced the agent?
- Given ADK's language implementations are kept in lockstep, does the choice between them for
  a CF-adjacent use case (e.g. Go, to match CF's own codebase — see kagent's Go-vs-Python
  cold-start tradeoff in `kagent.md`) come down purely to ecosystem fit with the surrounding
  platform, or are there framework-level differences worth weighing?
