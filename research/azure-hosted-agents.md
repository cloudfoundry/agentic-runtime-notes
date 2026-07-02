---
title: "Azure Foundry — Hosted Agents Model"
author: Ruben Koster (@rkoster)
date: 2026-07-02
tags: [runtime-lifecycle, sandboxing-isolation, identity, observability-governance, ecosystem-survey]
cf_areas: [diego, capi, uaa]
status: draft
sources:
  - https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/hosted-agents
---

## Summary

Azure Foundry's hosted agents model runs agents as containerized workloads with per-session
VM-isolated sandboxes, a persistent filesystem, and scale-to-zero with stateful resume. Each
agent deployment gets a dedicated Microsoft Entra identity. The platform auto-injects
OpenTelemetry traces (see `opentelemetry-genai.md`) and natively supports A2A agent
delegation (see `a2a-protocol.md`), the Responses protocol (OpenAI-compatible), and an
arbitrary-payload Invocations protocol.

## Key findings

- **Isolation model**: Per-session VM-isolated sandboxes with a persistent filesystem
  (`$HOME` and `/files`). 15-minute idle timeout, 30-day maximum session lifetime.
- **Packaging**: Agents are container images pushed to ACR; the platform pulls, provisions
  compute, assigns identity, and exposes an endpoint.
- **Identity**: Each agent deployment gets a dedicated Microsoft Entra ID created
  automatically. On-behalf-of (OBO) user identity available via M365 channels.
- **Protocols**: Responses (OpenAI-compatible, platform-managed conversation history),
  Invocations (arbitrary JSON, long-running async), and A2A for agent-to-agent delegation.
- **Observability**: Built-in Application Insights; protocol libraries emit OTel traces by
  default using the GenAI semantic conventions.
- **Scaling**: Per-session, not per-replica — no replica count to configure; concurrent
  sandboxes bounded by active-session quota.

## CF relevance

Azure Foundry illustrates what a production-grade PaaS-hosted agent model looks like when
built from scratch with agents as first-class citizens. The container-packaging model
parallels CF's app deployment; the per-session isolation and stateful resume go beyond CF's
stateless process model; and the per-agent identity and auto-injected observability raise
questions about what a platform should provide vs. what each application must wire up itself.

## Open questions

- Could a session-scoped state persistence model be layered onto a stateless process model,
  or does it require a different lifecycle primitive?
- What would an "agent buildpack" look like — protocol libraries, OTel auto-instrumentation,
  identity bootstrap?
- How would A2A endpoints be exposed through a platform's routing layer?
- Is per-session VM isolation necessary, or can process-level isolation suffice for most
  agent workloads?
