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
---

## Summary

Microsoft Agent Framework (MAF) is Microsoft's open-source SDK (Python, .NET, and a
public-preview Go binding) for building individual AI agents and graph-based multi-agent
workflows. It is explicitly positioned as "the direct successor" to both
[AutoGen](https://github.com/microsoft/autogen) (multi-agent orchestration abstractions) and
[Semantic Kernel](https://github.com/microsoft/semantic-kernel) (enterprise-grade
state/telemetry/type-safety), built by the same Microsoft teams. It bundles agents, an
opinionated "harness" for long multi-step tasks, and explicit graph-based workflows with
checkpointing, MCP tool integration, and A2A hosting support — but notably, its durable/stateful
execution story runs on **Azure Durable Task Framework**, not Dapr.

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
- **Durable execution is via Azure Durable Task Framework, not Dapr**: durability,
  restartability, and long-running workflow state are delivered by a separate
  [`agent-framework-durable-extension`](https://github.com/microsoft/agent-framework-durable-extension)
  repo, built on the **Durable Task Scheduler** (Azure Durable Functions' backing engine),
  Azurite (Azure Storage emulator), and Redis — with Azure Functions as a hosting option.
  Despite the assumption that Microsoft would lean on Dapr (its own CNCF sandbox project) for
  this, no Dapr integration is mentioned anywhere in the MAF README, the durable extension
  repo, or the Microsoft Learn overview/workflow docs as of this research. This makes MAF's
  durability story architecturally distinct from **Dapr Agents** (see `dapr-agents.md`), which
  is Dapr-native (uses Dapr Workflows/Actors/state stores directly) — MAF instead ties its
  durability substrate to the Azure Durable Task ecosystem.
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
workflow graphs, tool/MCP integration, and A2A as the default set of primitives. Its choice to
build durability on Azure's own Durable Task substrate (rather than Dapr, a CNCF project
Microsoft also stewards) is a useful data point when comparing execution-substrate options for
CF — it suggests durable agent execution doesn't require Dapr specifically, just *some*
workflow/checkpoint engine, which could be Diego-native, Temporal, Dapr, or otherwise. The
declarative YAML agent definitions and Foundry one-line hosting also raise the recurring
question from other notes: what would a CF-native "agent packaging" story (buildpack,
manifest, or droplet analogue) look like for MAF-style agents.

## Open questions

- Does MAF's OpenTelemetry instrumentation actually conform to the GenAI semantic
  conventions, or is it a custom schema (see `opentelemetry-genai.md`)?
- Is the lack of Dapr integration a deliberate architectural choice (avoiding a dependency on
  a separate runtime) or simply not-yet-built? Worth revisiting as the durable extension
  matures.
- How does MAF's A2A hosting story compare to Azure Foundry's native A2A support
  (`azure-hosted-agents.md`) — is A2A exposed identically regardless of hosting target?
- If CF wanted to host MAF-based agents, would the Durable Task Scheduler dependency (Azure
  Storage emulator/Azurite, Redis) need a CF-native substitute, or can it run against
  self-hosted/OSS-compatible backends off Azure?
- How does the "Harness" (planning, context compaction, memory, tool approval) compare to
  similar batteries-included agent runtimes elsewhere in this research set — is this a
  reusable pattern platforms should expect to support generically?
