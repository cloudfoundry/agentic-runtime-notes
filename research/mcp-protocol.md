---
title: "Model Context Protocol (MCP) — Agent-to-Tool Interoperability"
author: Ruben Koster (@rkoster)
date: 2026-08-10
tags: [inter-agent-comms, identity, observability-governance, ecosystem-survey]
cf_areas: [capi, uaa]
status: draft
sources:
  - https://modelcontextprotocol.io/introduction
  - https://modelcontextprotocol.io/specification/2025-06-18
  - https://modelcontextprotocol.io/specification/2025-06-18/basic/transports
  - https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization
  - https://registry.modelcontextprotocol.io
  - https://github.com/modelcontextprotocol
  - https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/community/sep-guidelines.mdx
  - https://en.wikipedia.org/wiki/Model_Context_Protocol
  - https://arxiv.org/abs/2503.23278
  - https://techcrunch.com/2025/12/09/openai-anthropic-and-block-join-new-linux-foundation-effort-to-standardize-the-ai-agent-era/
ratings:
  platform-impact:
    value: 55
    note: 'CF can host HTTP services and secure them with UAA, but lacks a first-class MCP service type, registry, lifecycle management, and standardized tool authorization for agent workloads.'
  maturity:
    value: 78
    note: 'MCP has broad framework and vendor adoption, dated specifications, official SDKs and registry work, and Linux Foundation governance, although transport evolution and authorization guidance are still moving.'
  novelty:
    value: 55
    note: 'MCP newly standardizes model-facing tools, resources, prompts, capability negotiation, and sampling across vendors, while deliberately borrowing JSON-RPC, OAuth, and Language Server Protocol patterns.'
  actionability:
    value: 88
    note: 'CF can directly prototype a Streamable HTTP MCP server as a bound multi-instance app, validate audience-bound OAuth tokens through UAA, and document why stdio and session affinity do not fit that service model.'

---

## Summary

The Model Context Protocol (MCP) is an open standard, originally released by Anthropic in
November 2024, that standardizes how AI applications ("hosts") connect to external tools,
data sources, and prompt templates via a client-server architecture — solving the "N×M"
integration problem so both sides of a tool integration implement MCP once instead of every
AI app writing bespoke connectors for every tool. It is referenced as the tool-integration
mechanism in nearly every other agent-framework note in this research set (Dapr Agents,
Google ADK, LangGraph, OpenAI Agents SDK, CrewAI, Letta, AWS Strands) but has not, until now,
had its own dedicated deep-dive. As of December 2025, Anthropic transferred stewardship to the
**Agentic AI Foundation (AAIF)**, a directed fund under the Linux Foundation co-founded by
Anthropic, Block, and OpenAI — moving MCP from single-vendor-led to multi-stakeholder open
governance, mirroring how A2A already sits under the Linux Foundation (`a2a-protocol.md`). The
protocol is JSON-RPC 2.0-based, defines three server-exposed primitives (Tools, Resources,
Prompts) and three client-exposed primitives (Sampling, Roots, Elicitation), and layers an
OAuth 2.1-based authorization framework on top for remote/HTTP servers.

## Key findings

- **Origin**: created at Anthropic (engineers David Soria Parra and Justin Spahr-Summers) and
  announced November 25, 2024, explicitly inspired by the Language Server Protocol's
  message-flow design, to solve the N×M tool-integration problem.
- **Governance shift (December 2025)**: Anthropic donated MCP to the Agentic AI Foundation
  (AAIF), a directed fund under the Linux Foundation co-founded by Anthropic, Block, and
  OpenAI (with support from other companies) — moving it from Anthropic-led to a neutral
  multi-stakeholder foundation.
- **Formal spec change process**: MCP now uses a **Specification Enhancement Proposal (SEP)**
  process (analogous to Python's PEPs), with SEP types (Standards Track, Informational,
  Process, Extensions Track), a defined status lifecycle, Core Maintainer review meetings
  every two weeks, required prototype implementations, and — for Standards Track SEPs with
  observable protocol behavior — mandatory conformance test scenarios in a dedicated
  conformance repo before a SEP can reach "Final."
- **Core architecture — host/client/server**: a **Host** is the LLM application that
  initiates connections; a **Client** is a connector instance living inside the host,
  maintaining a 1:1 stateful connection to one server; a **Server** provides
  context/capabilities. One host can run multiple clients to connect to multiple servers
  simultaneously.
- **Base protocol and transports**: messages are JSON-RPC 2.0, UTF-8 encoded, over a stateful
  connection with explicit capability negotiation during an initialization handshake. Two
  current standard transports: **stdio** (client launches server as a subprocess;
  newline-delimited JSON-RPC over stdin/stdout) and **Streamable HTTP** (single HTTP endpoint
  supporting POST+GET, optional SSE streaming, resumable streams via `Last-Event-ID`, session
  management via `Mcp-Session-Id` header). The prior **HTTP+SSE** transport (two separate
  SSE/POST endpoints) is deprecated but backward-compatibility guidance is still specified.
- **Server-exposed primitives**: **Tools** (model-callable functions/arbitrary code
  execution), **Resources** (contextual data/files for user or model use), **Prompts**
  (reusable templated messages/workflows for users).
- **Client-exposed primitives**: **Sampling** (lets a server request the client/host trigger a
  further LLM completion — recursive agentic behavior, with the protocol intentionally
  limiting server visibility into the prompt), **Roots** (lets a server ask about
  URI/filesystem boundaries it should operate within), **Elicitation** (lets a server request
  additional info from the user mid-interaction).
- **Authorization model**: for HTTP-based transports (optional for stdio, which should
  instead pull credentials from the environment), MCP defines an OAuth 2.1-based framework
  built on RFC 9728 (OAuth 2.0 Protected Resource Metadata — required for servers to advertise
  their authorization server), RFC 8414 (Authorization Server Metadata), RFC 7591 (Dynamic
  Client Registration, recommended), and RFC 8707 (Resource Indicators — clients must include
  a `resource` parameter binding tokens to the specific canonical MCP server URI to prevent
  token misuse/confused-deputy attacks). The spec explicitly forbids token passthrough and
  mandates PKCE; this authorization model was significantly tightened in the 2025-06-18 spec
  revision versus the original 2024-11-05 release.
- **Discovery / registry**: an official community-driven **MCP Registry**
  (`registry.modelcontextprotocol.io`, ~7.1k GitHub stars) lets clients discover published MCP
  servers; discovery for HTTP servers otherwise relies on OAuth Protected Resource Metadata
  (`.well-known/oauth-protected-resource`) for locating the authorization server.
- **Relationship to A2A**: MCP and A2A are explicitly billed as complementary layers of the
  agentic stack — "MCP connects agents to tools, A2A connects agents to agents"
  (`a2a-protocol.md`) — with A2A handling agent-to-agent task delegation/discovery via Agent
  Cards, while MCP standardizes how any single agent/host calls out to tools and data.
- **Ecosystem adoption**: OpenAI officially adopted MCP in March 2025 (ChatGPT desktop app,
  later ChatGPT Apps/dev-mode third-party server support); Google DeepMind announced adoption
  in April 2025; Microsoft supports MCP via Semantic Kernel and Azure OpenAI; Cloudflare
  supports deploying MCP servers; Salesforce began routing agent interactions via MCP in
  April 2026. Official SDKs exist for 11 languages (TypeScript, Python, Java, Kotlin, C#, Go,
  PHP, Ruby, Rust, Swift), several co-maintained with vendors (Microsoft/C#, Google/Go,
  JetBrains/Kotlin, PHP Foundation).
- **Security criticisms**: security researchers (April 2025) identified multiple concern
  classes — **prompt injection** via untrusted tool descriptions/metadata that the model reads
  as instructions; **tool poisoning**, where malicious/compromised servers advertise deceptive
  tool descriptions to exfiltrate data through other connected tools; and the **confused
  deputy problem**, where an MCP server acting as a proxy to a third-party API can be tricked
  into misusing a token/credential on behalf of an attacker. The current spec directly
  addresses these with explicit "Security and Trust & Safety" requirements (mandatory user
  consent before tool invocation, treating tool annotations as untrusted unless from a trusted
  server, prohibition on token passthrough, mandatory audience validation of access tokens).

## CF relevance

MCP is the connective tissue underlying almost every other framework note in this research
set — any CF-hosted agent runtime will almost certainly need to consume and/or expose MCP
servers as a baseline capability, the same way HTTP is a baseline expectation for web apps
today. Its OAuth 2.1-based authorization model (resource-bound tokens, no token passthrough,
mandatory audience validation) is directly relevant to `open-agent-auth.md`'s questions about
agent-to-agent/agent-to-tool trust boundaries, and gives CF a concrete, standards-based
pattern to evaluate rather than inventing one from scratch. Several framework notes in this
set flag MCP's stdio transport as poorly suited to scaled, multi-instance deployments (session
affinity, process lifecycle) — a concrete constraint CF should account for if it ever offers
"MCP server" as a bindable service type, favoring Streamable HTTP-based servers for
multi-instance CF apps. The recent governance handoff to a neutral foundation (mirroring A2A)
is also a positive signal for long-term platform investment, versus betting on a
single-vendor-controlled protocol.

## Open questions

- Should CF define a first-class "MCP server" service-binding type (analogous to a database
  service), so any CF app can declare and be granted scoped access to specific MCP tools —
  and if so, how would this interact with the OAuth 2.1 resource-indicator model to avoid
  confused-deputy risks across spaces/orgs?
- Given the stdio transport's documented unsuitability for scaled deployments, should CF
  actively discourage or disallow stdio-based MCP servers as CF-hosted workloads, steering
  developers toward Streamable HTTP from the start?
- How should CF's platform-level security posture treat the "tool poisoning" and
  prompt-injection risks called out in MCP's own spec — is this purely an application-level
  concern, or does CF need platform-level tooling (e.g., a vetted registry of approved MCP
  servers, akin to a buildpack registry) to mitigate supply-chain risk?
- With MCP now under neutral Linux Foundation governance (AAIF) alongside A2A, is there an
  opportunity for CF to participate directly in the specification process (via the SEP
  mechanism) if platform-specific gaps are identified?
