---
title: "Obot: Governed AI Gateways, Registries, and Hosted Agents"
author: Ruben Koster (@rkoster)
date: 2026-09-17
tags: [governance, authorization, agent-runtime, ecosystem-survey]
cf_areas: [uaa, capi, diego, loggregator]
status: draft
ratings:
  platform-impact:
    value: 86
    note: "Obot combines gateway, identity, catalog, hosted execution, and audit capabilities that resemble a platform-level control plane for AI workloads."
  maturity:
    value: 72
    note: "The project is an active open-source platform with broad capabilities, but deployment and multi-tenant operating choices require careful evaluation."
  novelty:
    value: 68
    note: "Obot's distinctive scope is the combination of MCP and LLM gateways, skills registries, hosted sandboxes, user-device controls, and correlated governance."
  actionability:
    value: 82
    note: "The capability split maps directly to potential CF shared services, bindings, policy integration, sandbox execution, and audit requirements."
sources:
  - https://github.com/obot-platform/obot
  - https://raw.githubusercontent.com/obot-platform/obot/main/README.md
  - https://github.com/obot-platform/obot/tree/main/docs
  - https://github.com/obot-platform/obot/tree/main/chart
---

## Summary

Obot is an open-source platform for organizations to manage, secure, and govern AI
ecosystems. It combines MCP and LLM gateways, hosted sandboxed MCP servers and agents,
identity and credential services, curated MCP and Skills registries, and correlated audit logs
across hosted services and user devices. For Cloud Foundry, Obot is a useful reference for a
shared AI governance layer, while its hosted execution capabilities would require explicit
sandbox, lifecycle, egress, and observability integration.

## Key findings

- **Obot is a platform rather than only a proxy.** Its documented scope includes controlled
  access to models and tools, hosted AI workloads, approved MCP servers and skills, credentials,
  access policy, and activity recording. It does not require an organization to standardize on
  one AI client, model provider, or tool ecosystem.
- **The MCP Gateway centralizes tool access.** It can proxy hosted or external MCP servers,
  compose selected tools from multiple servers, restrict server and tool access by users or
  identity-provider groups, manage MCP OAuth and shared credentials, and apply MCP or webhook
  filters that inspect, reject, or modify requests and responses.
- **The LLM Gateway centralizes model access.** It presents provider-compatible endpoints for
  providers such as OpenAI, Anthropic, Bedrock, Azure, and generic Responses-compatible APIs.
  Provider credentials remain in Obot, clients authenticate with scoped Obot API keys, model
  visibility is controlled by Model Access Policies, and requests, responses, sessions, token
  usage, and estimated cost can be recorded.
- **Hosted execution is isolated from the main server.** Obot can run `npx`, `uvx`, and
  containerized MCP servers as Docker containers or Kubernetes workloads, and can run hosted
  agents in similar isolated environments. Domain-based egress rules can be applied through a
  configured network-policy provider.
- **Deployment trust boundaries matter.** The repository documents a Docker development setup
  that mounts the host Docker socket so Obot can launch sibling containers, but recommends
  Kubernetes for production or multi-tenant installations. The socket approach should therefore
  be treated as a trusted single-tenant or evaluation configuration, not a general sandbox
  boundary.
- **Skills are managed alongside MCP servers.** Obot can curate MCP and Skills catalogs or
  index Git-backed repositories, expose MCP catalogs through the standard MCP Registry API,
  publish approved entries to clients, control access to entries or repositories, and reuse
  centrally managed Git credentials across catalog sources.
- **User-device and server controls are complementary.** Desktop agents and tools connect to
  Obot gateways, while Obot Sentry scans, audits, and enforces policy on AI activity on the
  device. The Obot CLI helps users and AI clients discover, install, and manage approved MCP
  servers and skills. These controls complement Obot Server's hosted gateway and execution
  services rather than replacing them.
- **Identity and governance are cross-cutting services.** Obot supports configured identity
  providers, platform roles and permissions, access control for servers, tools, skills, models,
  and administrative APIs, scoped credentials for clients and workloads, and restricted access
  to sensitive audit content.
- **The audit model is correlated across the platform.** Obot describes recording activity from
  hosted services and user devices, including client and session metadata, model token usage,
  estimated cost, and MCP activity. This is an important distinction from only collecting
  process logs from an agent runtime.
- **Obot integrates with external infrastructure.** The platform connects to remote MCP
  servers, model providers, S3-compatible object storage, Git providers, and authentication
  providers. Its registries and gateways therefore form policy boundaries around systems that
  remain outside Obot's own runtime.
- **The project spans different runtime responsibilities.** Gateways and registries govern
  access; hosted sandboxes execute servers and agents; identity and policy services determine
  who may use them; and audit services record activity. Treating these as separate operational
  planes is useful when comparing Obot to a platform such as Cloud Foundry.

## CF relevance

Cloud Foundry could use the Obot model as a reference for a shared AI platform service. A
platform-operated MCP Gateway and LLM Gateway could keep provider credentials out of
application environments, expose approved tools and models through service bindings, enforce
space or organization policy, and provide a consistent audit trail. CAPI could manage the
lifecycle of gateway instances or service offerings, while UAA or an external identity
provider could supply user and workload identity.

Obot's hosted execution plane is the harder mapping. A CF application can host a gateway or
registry service under Diego, but hosting untrusted MCP servers and agents requires a stronger
and more explicit sandbox boundary, domain egress control, resource quotas, and lifecycle model.
The platform could run trusted hosted workloads as ordinary CF apps, use a separate sandbox
substrate such as microVMs or gVisor, or integrate with Kubernetes as Obot does. Those choices
have different consequences for startup latency, density, tenant isolation, and operational
ownership.

The registry and governance pieces map naturally to platform services. Git-backed catalogs could
be exposed as approved service content, with credentials stored in a platform secret system and
access controlled by org or space policy. Loggregator-compatible events could correlate gateway
requests, model usage, MCP tool calls, hosted workload identity, policy decisions, and estimated
cost. The key CF design question is whether these functions should be one integrated product or
separate brokered services with stable interfaces.

## Open questions

- Should Cloud Foundry offer a shared Obot-like AI governance service, or expose separate MCP
  gateway, LLM gateway, registry, sandbox, and audit services?
- Which credentials should be platform-managed and injected through bindings, and which should
  remain application- or user-owned?
- Can Diego's existing isolation model safely host arbitrary MCP servers and agents, or is a
  microVM/gVisor substrate required for multi-tenant hosted execution?
- How should domain egress policy, private network access, and model/tool endpoint allowlists
  integrate with CF networking and application security groups?
- How should skills and MCP catalogs be curated, versioned, scanned, approved, and scoped to
  organizations, spaces, users, or agent identities?
- What identity should a hosted agent present to the gateways, and how should its permissions
  differ from the human or application that launched it?
- Which audit data belongs in Loggregator, which belongs in a durable governance store, and how
  should sensitive prompts, tool arguments, and model responses be protected?
- How should CF handle gateway and registry availability, credential rotation, provider
  outages, policy changes, and revocation while agent sessions are active?
