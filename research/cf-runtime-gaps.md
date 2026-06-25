---
title: Cloud Foundry gaps and friction points for AI agents
author: Ruben Koster (@rkoster)
date: 2026-06-25
tags: [ecosystem-survey, autoscaling, identity, sandboxing-isolation, inter-agent-comms, observability-governance, runtime-lifecycle]
cf_areas: [diego, capi, uaa, loggregator, routing, buildpacks]
status: draft
sources:
  - https://github.com/cloudfoundry/community/blob/main/toc/working-groups/agentic-runtime.md
---

> **This is the worked example note.** It shows the expected format and depth. Use it as a
> reference when writing your own — see [`../CONTRIBUTING.md`](../CONTRIBUTING.md).

## Summary

Cloud Foundry's runtime, routing, autoscaling, and observability stack is heavily optimized
for stateless HTTP applications. AI agents and LLM-powered workloads stress a different set
of assumptions — background workers, session state, per-agent identity, non-HTTP protocols,
and bursty scale-to-zero demand. This note catalogs seven gaps where CF's current
primitives create friction for agentic workloads, as a starting map for the research phase.

## Key findings

- **Async worker observability.** CF's observability, routing, and autoscaling are
  HTTP-biased. Frameworks like CrewAI and AutoGen rely on background worker queues (e.g.
  Celery) because of web-request timeouts, and CF has no native queue-depth autoscaling
  (compared with Kubernetes KEDA).
- **Session-stateful workloads.** CF apps are stateless by default. There is no native
  session persistence with auto-resume (unlike Azure's per-session VM sandboxes); state
  must be externalized to bound services, which works but isn't integrated.
- **Agent identity model.** CF identity is app-centric (manifest `name`, service bindings),
  with no per-agent identities, no agent-to-agent authentication, and no native agent
  discovery.
- **Protocol diversity.** Agents use A2A, AG-UI (bidirectional streaming), MCP, webhooks,
  and custom streaming protocols. CF routing is HTTP-centric; WebSockets/SSE are supported
  but there's no abstraction for non-HTTP agent protocols.
- **Buildpack ecosystem.** No AI/agent-specific buildpacks exist — no standard packaging
  for LangGraph/CrewAI/LlamaIndex, no OTel GenAI auto-instrumentation, no agent entrypoint
  convention.
- **Scaling model.** CF's min/max-instance model doesn't match bursty agent demand; there's
  no scale-to-zero with warm resume (Azure's per-session model) versus CF's per-replica
  scaling.
- **Tool access & MCP integration.** Agents need to discover and call tools (databases,
  APIs, MCP servers), but CF's service-binding model targets services, not tools, and MCP
  servers must be deployed as apps with manual routing.

| Gap | CF current state | What's needed |
|-----|------------------|---------------|
| Async worker observability | HTTP-biased | Queue-depth autoscaling, worker metrics |
| Session state | Stateless apps | Session persistence with auto-resume |
| Agent identity | App-centric | Per-agent identities, agent discovery |
| Protocol diversity | HTTP-centric | A2A, AG-UI, MCP routing |
| Buildpacks | No AI buildpacks | Agent framework buildpacks, OTel auto-instrumentation |
| Scaling | Per-replica | Per-session scaling, scale-to-zero with warm resume |
| Tool access | Service bindings | Tool discovery, MCP integration |

## CF relevance

Each gap points at a CF component that may need to evolve for agentic workloads: Diego and
CAPI for lifecycle/scaling and sandboxing, UAA for agent identity, Loggregator and OTel
conventions for observability, the routing tier for non-HTTP protocols, and the buildpack
ecosystem for packaging and instrumentation. Several gaps overlap (identity underpins both
agent-to-agent comms and tool access), which makes them good candidates for theme
clustering at the workshop.

## Open questions

- Which gaps are most urgent for real agent workloads people are trying to run on CF today?
- Where should a gap be closed by CF platform changes versus solved with buildpacks,
  services, or conventions on top of existing primitives?
- Which gaps are interdependent enough to belong to a single theme/POC track?
