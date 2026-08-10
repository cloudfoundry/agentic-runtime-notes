---
title: "Dapr Agents — Durable Agent Framework on Dapr"
author: Ruben Koster (@rkoster)
date: 2026-08-10
tags: [orchestration, inter-agent-comms, runtime-lifecycle, autoscaling, ecosystem-survey]
cf_areas: []
status: draft
sources:
  - https://github.com/dapr/dapr-agents
  - https://docs.dapr.io/developing-ai/dapr-agents/
  - https://docs.dapr.io/developing-ai/dapr-agents/dapr-agents-core-concepts/
  - https://docs.dapr.io/developing-ai/dapr-agents/dapr-agents-patterns/
  - https://docs.dapr.io/developing-ai/dapr-agents/dapr-agents-why/
  - https://docs.dapr.io/developing-ai/dapr-agents/dapr-agents-integrations/
---

## Summary

Dapr Agents is a Python framework (v1.0, GA) for building LLM-powered autonomous agents
on top of the Dapr runtime, rather than reimplementing distributed-systems primitives
(state, messaging, retries, service discovery) the way many agent frameworks do. Its
central contribution is the `DurableAgent`: an agent whose reasoning loop — LLM calls,
tool calls, and multi-turn state — runs as a Dapr Workflow backed by virtual actors, so
execution survives crashes, retries deterministically, and can idle down to zero cost
between turns. On top of that it adds multi-agent orchestration (pub/sub broadcast +
an agent registry), zero-config MCP tool discovery, and a hook system for
human-in-the-loop approval gates.

## Key findings

- **Agent execution is a Dapr Workflow, not just a Python loop**: `DurableAgent`
  dynamically creates a workflow per interaction, where each LLM call and tool
  execution is a durable *activity*. If a node crashes mid-task, the workflow resumes
  exactly where it left off rather than restarting or losing state. The older `Agent`
  class (synchronous, in-process, no workflow) is deprecated as of v1.0.0-rc.1 in favor
  of `DurableAgent` for all new development — the project is explicitly steering users
  toward the durable model.
- **Actors are the scale-to-zero mechanism**: Dapr Agents builds on Dapr's Workflow API,
  which itself runs on Dapr's virtual actor model. Each agent instance is a thread-safe,
  single-unit actor; idle agents are reclaimed but retain state, and the README claims
  "thousands of agents... on a single core" with "double-digit millisecond latency"
  resuming from zero. This is a stronger scale-to-zero story than typical container
  cold-start, because the state lives in the actor/state-store layer, not in a running
  process.
- **Retry/fault-tolerance is two-layered**: (1) `WorkflowRetryPolicy` on the
  `DurableAgent` itself (max attempts, exponential backoff, overall retry timeout) governs
  workflow-level retries; (2) underneath that, Dapr's own
  [resiliency policies](https://docs.dapr.io/operations/resiliency/resiliency-overview/)
  (timeouts, retry/backoff, circuit breakers) can be applied by platform operators to the
  state store or message broker components an agent uses, independent of application code.
- **Multi-agent orchestration is pub/sub + a registry, not a bespoke bus**: agents
  subscribe to a `pubsub` topic (`AgentPubSubConfig`) and register themselves in an
  `AgentRegistryConfig` backed by a Dapr state store; a separate `Orchestrator` process
  (Random, RoundRobin, or `LLMOrchestrator`) picks which registered agent handles the next
  turn and can broadcast to the whole team over a shared topic. This is deliberately built
  from generic Dapr pub/sub + state building blocks rather than a proprietary agent bus.
- **MCP is a first-class, zero-config tool source**: if the local Dapr sidecar has any
  `MCPServer` resources configured, `DurableAgent` auto-discovers their tools via the
  sidecar's metadata API and `DaprMCPClient`, with no `tools=` argument needed. Each
  discovered MCP tool call is scheduled as a *child workflow*
  (`dapr.internal.mcp.<server>.CallTool.<tool>`), so MCP tool invocations get the same
  durability/retry guarantees as native tools.
- **Interop with other agent frameworks is via "agents as tools," not a shared protocol**:
  the docs describe composing a `DurableAgent`'s reasoning loop with agents from OpenAI
  Agents SDK, LangGraph, or CrewAI by wrapping them as callable tools — a compositional
  rather than protocol-level integration. No explicit A2A (Agent2Agent protocol) support
  was found in the README or docs surveyed; multi-agent comms are Dapr pub/sub-native
  instead.
- **Human-in-the-loop via workflow suspension**: a `before_tool_call` hook can return
  `RequireApproval(...)`, which suspends the workflow on `wait_for_external_event` and
  publishes an approval-request event (HTTP, pub/sub, or workflow event); the workflow
  rehydrates on approve/deny or auto-denies on timeout. Because this is workflow-level
  suspension, the pause can last seconds to days without holding a process open.
- **Governance**: the README states Dapr Agents is "an open-source project under the
  CNCF umbrella" — it rides on Dapr's own CNCF-graduated status rather than being
  independently graduated itself; worth confirming its exact governance/maturity level
  if that matters for adoption decisions.

## CF relevance

The `DurableAgent`-on-actors model is a concrete answer to "how do you keep an
agent's mid-task state durable across restarts without a long-lived process" — relevant
regardless of whether CF ever adopts Dapr itself, as a reference architecture for
workflow-durable execution. The registry + pub/sub orchestration pattern (rather than a
special-purpose agent bus) is a reusable idea: CF's routing/service-discovery layer could
plausibly play the same role that Dapr's state store + pub/sub play here. Not sure how
Dapr's actor placement/sidecar model would map onto CF's process/instance model, or
whether it's even desirable to bring in another sidecar alongside CF's existing ones —
worth comparing against `research/dapr.md` for the base-runtime tradeoffs.

## Open questions

- Is a Dapr sidecar-per-app model (needed for actors/workflows/MCP auto-discovery)
  compatible with, or redundant with, CF's existing per-app sidecar patterns (e.g. Envoy)?
- The "thousands of agents on a single core" scale-to-zero claim rests on Dapr's actor
  placement service — how does that placement service behave under CF-style multi-tenant
  isolation, and does state-store-backed "identity" for an idle actor need the same
  security scrutiny as a running process?
- Given `DurableAgent` supersedes the non-durable `Agent`, is there a lighter-weight,
  non-Dapr-workflow execution mode worth studying separately, for agents that don't need
  cross-restart durability?
- How does the "agents as tools" composition pattern (wrapping LangGraph/CrewAI/OpenAI
  Agents as tools) compare to protocol-based interop like A2A or MCP — is one clearly
  better suited to a platform-level integration point?
- What does Dapr Agents' "CNCF umbrella" status actually mean in terms of governance,
  release cadence, and long-term support commitments, compared to Dapr core itself?
