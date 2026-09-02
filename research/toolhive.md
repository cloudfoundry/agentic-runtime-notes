---
title: "ToolHive — Secure Runtime and Gateway for MCP Servers"
author: Ruben Koster (@rkoster)
date: 2026-08-17
tags: [mcp, security, sandboxing, auth, gateway, ecosystem-survey]
cf_areas: [diego, capi, uaa]
status: draft
sources:
  - https://github.com/stacklok
  - https://github.com/stacklok/toolhive
  - https://docs.stacklok.com/toolhive/concepts/mcp-primer
  - https://docs.stacklok.com/toolhive/concepts/auth-framework
ratings:
  platform-impact:
    value: 58
    note: 'Initial review of ToolHive — Secure Runtime and Gateway for MCP Servers: its subject and tags indicate how broadly the capability could affect an agentic platform.'
  maturity:
    value: 76
    note: 'Initial review of ToolHive — Secure Runtime and Gateway for MCP Servers: this score reflects the amount of established external practice visible in the note.'
  novelty:
    value: 62
    note: 'Initial review of ToolHive — Secure Runtime and Gateway for MCP Servers: this score reflects how distinct or emerging the approach appears in the current landscape.'
  actionability:
    value: 58
    note: 'Initial review of ToolHive — Secure Runtime and Gateway for MCP Servers: this score reflects how readily the material could guide a focused experiment or follow-up.'

---

## Summary

[Stacklok](https://github.com/stacklok)'s flagship open source project, [ToolHive](https://github.com/stacklok/toolhive),
runs and manages [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) servers. Each
MCP server runs in an isolated container with a minimal permission profile, fronted by a gateway
that centralizes authentication, authorization, and observability. ToolHive ships as a CLI,
a desktop UI, and a Kubernetes operator, targeting individual developers through platform
teams and enterprises.

## Key findings

- **Per-server container isolation, no local credentials**: every MCP server runs in its own
  container with a minimal permission file rather than direct access to the host or the
  developer's credentials. This is the baseline security posture, independent of any gateway
  or auth configuration.
- **Gateway centralizes what the MCP spec leaves to each server**: the [official MCP spec](https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization)
  defines an OAuth 2.1 resource-server profile for HTTP transports (PKCE, audience-bound tokens,
  Protected Resource Metadata), but implementing it correctly — discovery, dynamic client
  registration, token validation, audience binding — is a lot to ask of every individual server
  author. ToolHive sits in front of MCP servers as a gateway and absorbs that complexity once,
  centrally.
- **Frontend/backend auth split**: ToolHive draws an explicit line between **frontend**
  authentication (client → MCP server, i.e. "who is calling this tool") and **backend**
  authentication (MCP server → upstream API, e.g. a GitHub MCP server's own token for the GitHub
  API). The two are handled by separate mechanisms rather than conflated.
- **Cedar for authorization**: authentication (identity) and authorization (what an authenticated
  identity may do) are deliberately separated. Access policy is expressed in
  [Cedar](https://www.cedarpolicy.com/), evaluated by a dedicated authorizer, deny-by-default,
  and version-controllable independent of server code.
- **Kubernetes Operator**: `MCPServer` and registry CRDs, multi-namespace support,
  container-based isolation, OIDC/OAuth SSO, secure token exchange, audit logging, OpenTelemetry
  traces, and Prometheus metrics — the closest analog here to a platform-native deployment model
  for agent tooling.
- **Registry Server as a governance point**: a curated catalog of MCP servers (own + upstream
  official registry) with provenance verification and signing, aimed squarely at the "shadow MCP"
  problem — developers standing up ungoverned MCP servers outside any security review.
- **Ecosystem context**: as of December 2025, MCP is a Linux Foundation project under the new
  Agentic AI Foundation (Anthropic, AWS, Block, Bloomberg, Cloudflare, Google, Microsoft, OpenAI
  as founding platinum members); Stacklok is a Silver AAIF member and active spec contributor.
  Transport-wise, MCP has converged on **stdio** (local, subprocess, newline-delimited JSON-RPC)
  and **Streamable HTTP** (remote, JSON-RPC over HTTP + optional SSE push), replacing the earlier
  HTTP+SSE transport.

## CF relevance

MCP is becoming a default way agents discover and call tools, which makes "run MCP servers
safely" a variant of the core agentic-runtime problem: how does the platform sandbox a
tool-calling process, mediate its identity and permissions, and give operators visibility into
what it did? ToolHive's model maps loosely onto CF-native concepts — per-server container
isolation is conceptually similar to a Diego container/app instance, its Cedar-based authZ policy
plays a role similar to UAA scopes, and the Registry Server's curated-catalog-with-governance
approach echoes CAPI's service broker/marketplace model. Whether these map cleanly or just
rhyme is exactly the kind of question this working group would want to dig into.

## Open questions

- Does Cedar-based policy authorization compose with or duplicate UAA scopes/CAPI roles, or
  would a CF integration want to translate one into the other?
- The Kubernetes Operator is the most fleshed-out deployment story; how much of that model
  (CRDs, multi-namespace isolation, OTel/Prometheus wiring) would need to be reinvented for a
  Diego-backed (non-Kubernetes) CF deployment, versus reused as-is for CF-on-Kubernetes?
- ToolHive's backend-auth handling (MCP server → upstream API credentials) looks like it overlaps
  with CF's existing service-binding model — is there a natural integration point, or would they
  conflict?
- The registry/provenance/signing story for MCP servers is still early across the ecosystem —
  is there a CF-specific angle (e.g. tying into existing buildpack/OCI signing tooling) worth
  tracking?
