---
title: "Agent Router: Envoy-Based Control Plane for AI Traffic"
author: Ruben Koster (@rkoster)
date: 2026-09-17
tags: [routing, observability-governance, agent-runtime, ecosystem-survey]
cf_areas: [capi, diego, loggregator]
status: draft
ratings:
  platform-impact:
    value: 78
    note: "A shared AI gateway could centralize provider access, quotas, credentials, and usage attribution for many CF applications."
  maturity:
    value: 76
    note: "The project is an active Apache-2.0 Envoy-based system with a Kubernetes deployment model and a standalone CLI, but the CLI is documented as experimental."
  novelty:
    value: 58
    note: "The distinctive contribution is applying Envoy Gateway and an external processor to model-aware routing and token accounting rather than introducing a new agent workflow model."
  actionability:
    value: 72
    note: "The standalone router can be evaluated quickly, while adapting the Kubernetes control plane to CF would require a deliberate platform integration design."
sources:
  - https://github.com/theagentrouter/agent-router
  - https://github.com/theagentrouter/agent-router/blob/main/LICENSE
  - https://theagentrouter.ai/docs/concepts/
  - https://theagentrouter.ai/docs/concepts/architecture/system-architecture
  - https://theagentrouter.ai/docs/concepts/architecture/control-plane
  - https://theagentrouter.ai/docs/concepts/architecture/data-plane
  - https://theagentrouter.ai/docs/concepts/resources
  - https://theagentrouter.ai/docs/getting-started/
  - https://theagentrouter.ai/docs/cli/
---

## Summary

Agent Router, formerly Envoy AI Gateway, is an Apache-2.0 open-source control plane for AI
and agent traffic. It gives applications one OpenAI-compatible interface while centralizing
provider routing, credentials, quotas, failover, and usage attribution. Its production
architecture is Kubernetes- and Envoy-based, with a standalone `aigw run` mode for local or
dependency-light evaluation.

## Key findings

- **The architecture separates control and data planes.** The Agent Router controller watches
  AI Gateway custom resources through the Kubernetes API, creates or manages Envoy Gateway
  resources, and fine-tunes xDS through the Envoy Gateway extension-server protocol. Envoy
  Gateway then applies the resulting configuration to the Envoy Proxy data plane.
- **The data plane is AI-aware rather than only an HTTP reverse proxy.** Envoy Proxy works
  with the AI Gateway External Processor and a Rate Limit Service. The external processor
  selects a provider from request paths, headers, and model names; transforms request and
  response formats; applies upstream authentication; and tracks token usage for streaming and
  non-streaming responses. The Rate Limit Service enforces budgets based on token consumption.
- **Three custom resources define the policy model.** `AIGatewayRoute` describes the unified
  client-facing API, routing rules, transformations, and possible cost tracking.
  `AIServiceBackend` represents a provider or other AI service endpoint. A
  `BackendSecurityPolicy` supplies backend authentication behavior, including API-key and AWS
  credential authentication.
- **The gateway fronts more than hosted model APIs.** The project presents one consistent
  interface for hosted providers, self-hosted inference, and MCP servers. Its documented
  two-tier pattern uses a centralized Tier One Gateway for authentication, top-level routing,
  and global rate limits, with a Tier Two Gateway providing finer-grained access to a
  self-hosted model-serving cluster.
- **There are two operational paths.** `aigw run` starts an OpenAI-compatible router locally
  without Docker or Kubernetes and can front providers, self-hosted models, and MCP servers.
  The production path installs Agent Router with Envoy Gateway in Kubernetes. This makes the
  local mode useful for experimentation, but the full controller, CRD, admission-webhook,
  xDS, and sidecar architecture remains Kubernetes-specific.
- **Agent Router is a gateway and policy layer, not an agent runtime.** It normalizes access
  to model and tool endpoints and can enforce traffic policy, but it does not replace an
  application's agent orchestration, memory, durable execution, or task-recovery logic.

## CF relevance

Agent Router suggests a useful shared-service boundary for Cloud Foundry: applications could
bind to one platform-operated AI gateway rather than each carrying provider-specific SDKs,
credentials, retry policy, and quota logic. A CF service binding could provide the gateway
endpoint and client credentials to an application, while provider credentials remain owned by
the platform operator. This would make provider rotation and centralized usage attribution
possible without distributing vendor keys across application spaces.

The standalone binary appears easier to operate as a CF application than the complete
Kubernetes installation. CF routing could expose the gateway endpoint, and Diego could
supervise the router process. However, ordinary HTTP routing is not equivalent to Agent
Router's model-aware processing: token accounting, provider-specific transformations,
failover, and token-based budgets require the external processor or equivalent gateway logic.
Those policies would also need clear tenant and space boundaries.

The production architecture exposes a more substantial integration question. Agent Router's
controller depends on Kubernetes APIs, CRDs, admission webhooks, Envoy Gateway, xDS, and
sidecar insertion. Running that unchanged would require a separate Kubernetes control plane,
not just a CF deployment. CF could instead provide a smaller adapter that translates a
platform service definition into Agent Router configuration, or adopt the architectural
pattern independently using CF routing, service bindings, and platform-managed policy
services. In either case, Loggregator-compatible metrics and logs, request-level cost
attribution, trace correlation, and credential isolation would need explicit design rather
than being assumed from the Envoy deployment.

## Open questions

- Should Cloud Foundry offer one shared AI gateway, a brokered service that teams provision,
  or only primitives that let application teams run their own gateway?
- Which provider credentials, model allowlists, quotas, and failover policies should be
  platform-managed, and which should remain application-owned?
- Should token-aware rate limiting and cost attribution be a CF platform capability, a
  gateway service capability, or an external service bound to applications?
- Is Kubernetes an acceptable dependency for the full Agent Router architecture, or would a CF
  integration need a native control plane that reconciles gateway policy without CRDs and
  admission webhooks?
- What interoperability boundary should CF standardize on: an OpenAI-compatible API, MCP
  gatewaying, A2A or another agent protocol, or a combination of these interfaces?
