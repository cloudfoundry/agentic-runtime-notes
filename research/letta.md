---
title: "Letta (formerly MemGPT) — Durable, Memory-Centric Stateful Agents"
author: Ruben Koster (@rkoster)
date: 2026-08-10
tags: [runtime-lifecycle, inter-agent-comms, ecosystem-survey]
cf_areas: []
status: draft
sources:
  - https://github.com/letta-ai/letta
  - https://arxiv.org/abs/2310.08560
  - https://docs.letta.com/concepts/stateful-agents
  - https://docs.letta.com/concepts/memfs
  - https://docs.letta.com/concepts/shared-memory
  - https://docs.letta.com/configuration/memory
  - https://docs.letta.com/configuration/subagents
  - https://docs.letta.com/configuration/models
  - https://docs.letta.com/platform/app-server
  - https://docs.letta.com/self-hosting
  - https://docs.letta.com/reference/terminology
  - https://docs.letta.com/agent-sdk/mcp
ratings:
  platform-impact:
    value: 65
    note: 'CF can host the App Server and bind storage, but has no durable, addressable agent identity or managed evolving-memory service equivalent to Letta agents, shared blocks, and MemFS.'
  maturity:
    value: 60
    note: 'Letta has an Apache-licensed implementation, 24k-plus stars, extensive history, self-hosting, and a hosted service, but its classic memory API is legacy while the product pivots to Letta Code and MemFS.'
  novelty:
    value: 78
    note: 'The MemGPT model lets an LLM page and edit its own context like virtual memory, while durable addressable agents and git-backed MemFS make memory and identity primary runtime abstractions.'
  actionability:
    value: 58
    note: 'A MemFS-backed agent-state binding and App Server isolation trial are plausible, but the ongoing V1-to-MemFS pivot and unrestricted filesystem and shell access leave substantial scoping work.'

---

## Summary

Letta (formerly MemGPT) is an Apache-2.0 project originating from a UC Berkeley research
paper — "MemGPT: Towards LLMs as Operating Systems" (Packer et al., Oct 2023) — that proposed
managing an LLM's limited context window the way an OS manages virtual memory, paging
information between an always-in-context tier and external storage. The research produced a
company, Letta AI, which productized the idea as an open-source "stateful agents" platform.
Unlike Dapr Agents, Microsoft Agent Framework, Temporal, kagent, or Google ADK — all of which
foreground workflow/orchestration — Letta's differentiating angle from day one has been
**agent memory and identity persistence**: an agent is a durable, addressable, server-side
entity with its own evolving memory, not an ephemeral chat session or workflow run. The
project is currently mid-pivot: the classic MemGPT-style REST API (core/archival/recall
memory) is now labeled "legacy"/"V1," and active development has moved to a CLI-first coding-
agent product ("Letta Code") built around a git-backed markdown memory filesystem called
MemFS, with a separate stateful App Server and a hosted Letta Cloud.

## Key findings

- **License, governance, origin**: Apache-2.0, ~24.2k GitHub stars, 2.6k forks, 7,469+
  commits, maintained by Letta AI. The repo is explicitly named "Letta (formerly MemGPT)"; the
  underlying research is the MemGPT paper (Packer, Wooders, Lin, Fang, Patil, Stoica, Gonzalez
  — UC Berkeley/RISELab, arXiv:2310.08560, first posted Oct 2023).
- **MemGPT (paper) vs. Letta (product)**: MemGPT is the research concept for *virtual context
  management* — treating the LLM context window as "fast memory" and external storage as "slow
  memory," with an OS-style paging mechanism the model calls itself to move data in and out of
  context. Letta is the company/framework that operationalized and renamed this system — docs
  still cite this lineage directly ("builds on our lab's latest research in AI memory and
  continual learning").
- **Core idea — LLM-as-OS / self-editing context**: the original design gives the model tools
  to edit its own context — a "core memory" segment always resident in the prompt, plus paging
  calls to move data to/from external "archival"/"recall" storage — explicitly modeled on OS
  virtual-memory paging rather than naive prompt truncation or summarization. This is the
  conceptual root of Letta's "stateful agents" positioning as distinct from orchestration
  frameworks.
- **Classic (V1/legacy) memory architecture — still documented**: three tiers matching the
  MemGPT paper almost 1:1 — memory blocks (core memory, always-in-context, agent-editable),
  archival memory (long-term, vector-searchable, agent pages information in/out via tool
  calls), and conversation search (recall memory — full-text/vector/hybrid search over past
  history). These are self-editing: the agent calls dedicated memory-editing tools rather than
  memory being externally managed.
- **New (current) memory architecture — MemFS, a git-backed context repository**: current
  Letta agents ("Letta Code" harness) store long-term memory as Markdown files with YAML
  frontmatter in MemFS, a git-backed filesystem the agent reads/writes/organizes itself. Files
  under `system/` are always loaded into the system prompt (≈ core memory); everything else is
  discoverable but lazily loaded only when relevant (≈ archival). Every memory edit is a git
  commit, giving version history and conflict resolution; MemFS has no built-in vector index by
  default — semantic/hybrid search requires a separate "MemFS Search" mod. This is a notably
  less "OS-paging," more "developer filesystem" framing than the original MemGPT metaphor.
- **"Dreaming" / sleep-time compute for memory consolidation**: background subagents
  periodically review recent conversations and consolidate lessons into MemFS without
  interrupting the active session — a scheduled/async analogue to the archival-memory-write
  step in the original MemGPT design.
- **Server architecture — durable, addressable agents, not in-process objects**: both eras
  position the agent as a server-side, durable entity closer to Orleans' virtual-actor model
  (`orleans.md`) or a database row than an in-process object. The current architecture centers
  on an always-on App Server exposing one bidirectional WebSocket; agent state (memory,
  messages) is decoupled from *where* the harness/tools execute (a "computer") — a
  cloud-hosted agent's identity can move between a laptop, a cloud sandbox, or a remote VM
  while its state stays in Letta Cloud. This is a stronger persistence/mobility guarantee than
  ADK's `Session`/`Runner` model (which centers on an in-process conversation object,
  `google-adk.md`) and conceptually adjacent to Orleans grains (location-transparent, always-
  addressable, backed by durable storage).
- **Multi-agent support is present but secondary to memory depth**: Letta supports subagents —
  a main agent can spawn specialized helpers (built-in types: `fork`, `general-purpose`,
  `history-analyzer`, `init`, `memory`, `recall`, `reflection`) to keep its own context clean,
  run in parallel/background mode, or be launched from custom Markdown+frontmatter
  definitions. Any existing full-featured Letta agent can be deployed as a subagent by ID, and
  a shared-memory feature lets multiple cloud-hosted agents attach the same git-backed context
  repository. This is closer to "memory-centric task delegation" than the graph-based
  multi-agent orchestration seen in Dapr Agents/ADK — there's no dedicated workflow-graph or
  routing layer.
- **Tool integration — function tools plus MCP (client-side)**: custom client tools plus MCP
  tools discovered from stdio, Streamable HTTP, or legacy SSE servers, namespaced as
  `mcp__<server>__<tool>`, with wildcard allowlisting. MCP connections run in the SDK host's
  process (not a managed sandbox), so a stdio filesystem MCP server sees the host's
  filesystem directly.
- **No A2A protocol support found**: neither the current docs nor the legacy V1 API reference
  mention the Agent2Agent protocol (contrast with Google ADK's first-class bidirectional A2A,
  `google-adk.md`, `a2a-protocol.md`). Letta does support an "ACP" (Agent Client Protocol)
  integration for editor clients like Zed — a different, editor-oriented protocol, not to be
  confused with A2A.
- **Deployment — self-hosted vs. Letta Cloud, legacy Docker path now deprecated**: the legacy
  stack documented a self-hosted Docker/Compose server backed by Postgres (now under
  "Deprecated" in docs nav). The current model offers: local/in-process CLI or desktop-app
  execution with on-disk state; a self-hosted App Server for centralizing/remote-exposing local
  agents (WebSocket auth via capability or signed bearer tokens); and Letta Cloud, a managed
  control plane where agent state lives remotely and can be "teleported" across execution
  environments. Self-hosting requires care: the App Server has full filesystem/shell access on
  its host and must never be exposed directly to untrusted clients.
- **Broad, explicitly model-agnostic provider support**: agents can switch models
  mid-conversation; supported providers include Anthropic, OpenAI, Google Gemini/Vertex, Azure
  OpenAI, Amazon Bedrock, Mistral, DeepSeek, Groq, Cerebras, Fireworks, Together AI,
  OpenRouter, xAI, and local inference via Ollama/LM Studio/llama.cpp, plus generic
  OpenAI-compatible gateways.
- **Observability is Letta-specific, not OTel-based**: the V1 API exposes per-step and per-run
  tracing as first-class resources, plus step-level metrics and feedback endpoints — a
  lighter-weight, Letta-specific tracing model rather than OTel GenAI semantic-convention
  instrumentation (contrast with ADK/Dapr Agents/MAF, all covered in
  `opentelemetry-genai.md`).
- **Adoption signals**: ~24.2k stars on the legacy server repo; the MemGPT paper
  (arXiv:2310.08560) is a foundational, widely-cited reference in the "LLM long-term memory"
  literature and predates most competing "agent memory" products. Letta Code was reportedly
  the "top OSS model-agnostic harness on Terminal-Bench" at release per Letta's own blog (not
  independently verified here).

## CF relevance

Letta is the one framework in this survey that treats agent identity/memory persistence as
the primary hard problem rather than a secondary concern bolted onto workflow orchestration —
directly relevant if CF's agentic-runtime investigation needs a data point on how to model
long-lived, addressable agent state, distinct from (but complementary to) the
workflow-durability concerns covered in `temporal.md`, `dapr-agents.md`, and `orleans.md`. The
mid-flight pivot from a classic stateless-server/Postgres/REST model to a CLI-first, git-
backed-filesystem model is itself a useful signal: even a memory-first project found the
"network service with a memory API" packaging insufficiently ergonomic for coding-agent use
cases, and moved toward local-first execution with optional cloud state sync — worth weighing
against any CF assumption that agent state should always live in a remote, centrally-hosted
store.

## Open questions

- Letta's server-side, addressable-agent model (agents as durable entities, location-
  transparent across execution environments) is conceptually close to Orleans grains
  (`orleans.md`) — is there a shared underlying pattern CF could adopt for "agent identity" as
  a platform primitive, independent of which memory architecture (MemGPT-style vs. MemFS)
  sits on top?
- MemFS's git-backed memory model gives free version history/audit trail for free — is this a
  more CF-native-friendly persistence mechanism (a directory + git, no database required) than
  the Postgres-backed model it replaced, worth prototyping against for an "agent state"
  service binding?
- Letta's explicit lack of A2A support, despite deep investment in memory/state, reinforces
  the pattern seen in LangGraph (`langgraph.md`) that A2A adoption is uneven — should CF treat
  A2A as an emerging-but-not-yet-universal standard when planning cross-framework
  interoperability?
- The App Server's full filesystem/shell access (explicitly warned against exposing to
  untrusted clients) raises the same sandboxing/isolation questions already flagged in
  `k8s-agent-sandbox.md` — how would a CF-hosted Letta agent's App Server be isolated from
  other tenants' workloads on the same platform?
