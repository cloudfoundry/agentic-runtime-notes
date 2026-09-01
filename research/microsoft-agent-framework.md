---
title: "Microsoft Agent Framework — Unified SDK for Agents and Multi-Agent Workflows"
author: Ruben Koster (@rkoster)
date: 2026-08-10
tags: [orchestration, inter-agent-comms, observability-governance, ecosystem-survey]
cf_areas: []
status: draft
sources:
  - https://github.com/microsoft/agent-framework
  - https://github.com/microsoft/agent-framework-durable-extension
  - https://learn.microsoft.com/en-us/agent-framework/overview/agent-framework-overview
  - https://learn.microsoft.com/en-us/agent-framework/user-guide/workflows/overview
  - https://github.com/microsoft/agent-framework/blob/main/dotnet/samples/02-agents/AgentProviders/dapr/Agent_With_Dapr/README.md
  - https://docs.diagrid.io/develop/agents/microsoft/
  - https://github.com/diagridio/dotnet-ai
  - https://github.com/diagridio/python-ai
---

## Summary

Microsoft Agent Framework (MAF) is Microsoft's open-source SDK (Python, .NET, and a
public-preview Go binding) for building individual AI agents and graph-based multi-agent
workflows. It is explicitly positioned as "the direct successor" to both
[AutoGen](https://github.com/microsoft/autogen) (multi-agent orchestration abstractions) and
[Semantic Kernel](https://github.com/microsoft/semantic-kernel) (enterprise-grade
state/telemetry/type-safety), built by the same Microsoft teams. It bundles agents, an
opinionated "harness" for long multi-step tasks, and explicit graph-based workflows with
checkpointing, MCP tool integration, and A2A hosting support. Dapr integration turns out to be
richer than it first appears: Microsoft's own sample uses Dapr only narrowly, as a pluggable
inference-backend provider, while its first-party durable-workflow story runs on **Azure
Durable Task Framework** — but a third-party library from **Diagrid** (Dapr's commercial
steward) instead builds MAF agents *directly atop Dapr's own Durable Workflows*, pub/sub, and
state store.

## Key findings

- **Explicit AutoGen + Semantic Kernel successor**: the docs state MAF "combines AutoGen's
  simple agent abstractions with Semantic Kernel's enterprise features — session-based state
  management, type safety, middleware, telemetry — and adds graph-based workflows for explicit
  multi-agent orchestration," and provides dedicated
  [migration guides from Semantic Kernel](https://learn.microsoft.com/en-us/agent-framework/migration-guide/from-semantic-kernel)
  and [from AutoGen](https://learn.microsoft.com/en-us/agent-framework/migration-guide/from-autogen).
- **Three capability tiers**: **Agents** (LLM-driven, call tools/MCP servers, dynamic
  step order), an opinionated **Harness** (batteries-included planning/todo-tracking, context
  compaction, file access/memory, "don't-ask-again" tool approval, observability for long
  multi-step tasks), and **Workflows** (graph of `executors` and `edges` with type-safe
  routing — an explicitly-defined, not LLM-improvised, execution path).
- **Orchestration patterns**: workflows support sequential, concurrent, hand-off, group
  collaboration, and "magentic" (AutoGen-lineage) multi-agent patterns, plus checkpointing,
  streaming, human-in-the-loop gates, and "time-travel" (replay/rewind of workflow state).
- **MCP and multiple model providers**: agents call tools and MCP servers directly, with
  provider support spanning Microsoft Foundry, Azure OpenAI, OpenAI, Anthropic, Ollama, and
  more — the framework is provider-agnostic by design ("provider flexibility so your
  architecture can evolve without major rewrites").
- **A2A and Foundry hosting**: the `04-hosting` samples cover A2A protocol hosting,
  "self-hosted protocol helpers," and one-line-ish deployment to Foundry-hosted infrastructure
  (see `azure-hosted-agents.md` for the Foundry hosted-agent runtime model this integrates
  with, and `a2a-protocol.md` for the protocol itself).
- **Dapr integration exists, but only as an inference-backend provider**: the
  [`Agent_With_Dapr`](https://github.com/microsoft/agent-framework/blob/main/dotnet/samples/02-agents/AgentProviders/dapr/Agent_With_Dapr/README.md)
  sample uses Dapr's **Conversation API** building block (`Dapr.AI.Microsoft.Extensions`,
  `AddDaprChatClient`) to route an agent's LLM calls through the Dapr sidecar to a
  `conversation.*` component (e.g. `conversation.ollama`) instead of calling a model
  provider's SDK directly. This buys provider portability (swap the backing LLM by swapping
  the Dapr component, not the app code) and built-in response caching (`cacheTTL` on the
  component). It is listed as one of a dozen-plus interchangeable "AgentProviders" (alongside
  OpenAI, Azure, Anthropic, Ollama, ONNX, GitHub Copilot, A2A, etc.) — i.e. Dapr is treated as
  a model-backend abstraction, not as MAF's orchestration or state substrate.
- **Durable *workflow* execution is via Azure Durable Task Framework, not Dapr**: separately
  from the inference-provider integration above, durability, restartability, and long-running
  workflow state for MAF's **Workflows** feature are delivered by a distinct
  [`agent-framework-durable-extension`](https://github.com/microsoft/agent-framework-durable-extension)
  repo, built on the **Durable Task Scheduler** (Azure Durable Functions' backing engine),
  Azurite (Azure Storage emulator), and Redis — with Azure Functions as a hosting option. No
  Dapr Workflows/Actors integration is mentioned for this layer in the MAF README, the durable
  extension repo, or the Microsoft Learn overview/workflow docs as of this research. This makes
  MAF's *workflow durability* story architecturally distinct from **Dapr Agents** (see
  `dapr-agents.md`), which is Dapr-native end-to-end (uses Dapr Workflows/Actors/state stores
  directly for both the agent loop and durability) — MAF only touches Dapr at the model-call
  edge, and ties its actual durability substrate to the Azure Durable Task ecosystem instead.
- **...unless you use Diagrid's Dapr-native durability layer for MAF**: Diagrid (the company
  founded by Dapr's original creators, and its primary commercial steward) publishes
  [`diagridio/dotnet-ai`](https://github.com/diagridio/dotnet-ai) (`Diagrid.AI.Microsoft.AgentFramework`
  on NuGet) — "a library that facilitates building agents using Microsoft's Agent Framework
  atop Dapr's Durable Workflows." This wraps MAF agent tasks in Dapr Workflows for automatic
  retries/checkpointing/crash recovery, uses Dapr pub/sub to decouple multi-agent
  communication, and uses a Dapr state store to persist chat memory across restarts — i.e. the
  complete Dapr-native durability story (workflows + actors/state + pub/sub) that Microsoft's
  own `agent-framework-durable-extension` does *not* provide. It reuses the same Conversation
  API mechanism as Microsoft's own sample (`AddDaprConversationClient()` +
  `conversationComponentName`), and per Diagrid's docs a conversation component is *required*,
  not optional, for this integration. This is a **third-party, Dapr-ecosystem-provided**
  durability path, not something shipped or endorsed in the core `microsoft/agent-framework`
  repo itself.
- **...but not on the Python side**: Diagrid's Python counterpart,
  [`diagridio/python-ai`](https://github.com/diagridio/python-ai) (pip package `diagrid`, part
  of the "Diagrid Catalyst" managed Dapr Workflow product), wraps **eleven** other agent
  frameworks in Dapr Workflows — LangGraph, CrewAI, Google ADK, Strands, PydanticAI, OpenAI
  Agents, Claude Agent SDK, LangChain, Smolagents, LangChain Deep Agents, and HolmesGPT — but
  conspicuously **not** Microsoft Agent Framework's Python binding, even though the .NET
  binding is covered by `dotnet-ai`. So the Dapr-native durability path for MAF is currently
  .NET-only; Python MAF users have no equivalent, despite Diagrid actively building out
  framework coverage elsewhere. This also reveals Diagrid's play more broadly: a
  framework-agnostic "bring your own agent framework, we supply the Dapr-backed durability"
  product, positioning Dapr Workflows as a universal durability substrate across the wider
  agent-framework ecosystem, not just Dapr's own `dapr-agents` or MAF specifically.
- **Observability built on OpenTelemetry**: "Built-in OpenTelemetry integration for
  distributed tracing, monitoring, and debugging" is listed as a first-class feature, with
  dedicated Python and .NET observability samples, though the README does not explicitly cite
  the GenAI semantic conventions by name (see `opentelemetry-genai.md`) — worth confirming
  whether MAF's span attributes actually conform to that spec.
- **Declarative agents**: agents can be defined in YAML "for faster setup and versioning,"
  suggesting a config-driven deployment path that could matter for platform-level agent
  packaging, similar in spirit to a buildpack/manifest model.
- **Positioning vs. LangGraph/CrewAI**: the README doesn't directly benchmark against
  LangGraph or CrewAI, but the "Is this the right framework for you?" section reads as an
  implicit contrast — MAF pitches itself at production use requiring durability,
  restartability, governance, and human-in-the-loop control, beyond a "stateless chat loop."

## CF relevance

MAF is a strong signal of where enterprise agent frameworks are converging: agents, explicit
workflow graphs, tool/MCP integration, and A2A as the default set of primitives. The three-way
split between Microsoft's own durability path (Azure Durable Task Framework), Microsoft's own
Dapr touchpoint (Conversation API only), and Diagrid's third-party Dapr-native durability layer
(Dapr Workflows + pub/sub + state store, .NET-only for MAF) is a useful data point for CF: it
shows a mature framework's durability substrate is *not* fixed to one vendor's stack — the
ecosystem, not just the framework author, can supply the durability/state layer, and a single
vendor (Diagrid) is actively productizing "durability-as-a-service" across a dozen-plus
competing agent frameworks. That decoupling (agent framework vs. durability substrate vs.
inference-backend abstraction, as three independently swappable concerns) may be a more useful
design reference for CF than any single implementation. The declarative YAML agent definitions
and Foundry one-line hosting also raise the recurring question from other notes: what would a
CF-native "agent packaging" story (buildpack, manifest, or droplet analogue) look like for
MAF-style agents.

## Open questions

- Does MAF's OpenTelemetry instrumentation actually conform to the GenAI semantic
  conventions, or is it a custom schema (see `opentelemetry-genai.md`)?
- Why does Microsoft's own first-party durability extension not use Dapr, when a third party
  (Diagrid) has already built a working Dapr Workflows-based alternative? Is this organizational
  (different teams, Azure-first bias) or a deliberate technical preference?
- How mature/supported is Diagrid's `dotnet-ai` integration compared to Microsoft's own
  `agent-framework-durable-extension` — is it production-grade, or a demonstration/marketing
  vehicle for Dapr? And why does `python-ai` cover eleven other frameworks but not MAF's Python
  binding — is MAF-Python support simply not built yet, or deliberately deprioritized?
- How does MAF's A2A hosting story compare to Azure Foundry's native A2A support
  (`azure-hosted-agents.md`) — is A2A exposed identically regardless of hosting target?
- If CF wanted to host MAF-based agents, would the Durable Task Scheduler dependency (Azure
  Storage emulator/Azurite, Redis) need a CF-native substitute — or could the Dapr-native path
  (Diagrid's library) be used instead, making Dapr (already covered in `dapr.md`) sufficient
  infrastructure for both the durability layer and the inference-backend abstraction? Would CF
  be better served by a Diagrid-style "durability-as-a-service" layered under many frameworks
  rather than betting on one framework's built-in durability story?
- How does the "Harness" (planning, context compaction, memory, tool approval) compare to
  similar batteries-included agent runtimes elsewhere in this research set — is this a
  reusable pattern platforms should expect to support generically?
