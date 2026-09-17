---
title: "MCP Apps: Interactive UIs Served by MCP Tools"
author: Ruben Koster (@rkoster)
date: 2026-09-17
tags: [inter-agent-comms, governance, ecosystem-survey]
cf_areas: [capi, uaa, diego]
status: draft
ratings:
  platform-impact:
    value: 72
    note: "Interactive tool UIs could make CF-hosted AI services more usable while preserving a governed MCP server boundary."
  maturity:
    value: 68
    note: "MCP Apps has an official specification and SDK repository with examples, but compliant host support remains an ecosystem concern."
  novelty:
    value: 76
    note: "The extension standardizes a server-declared UI resource and host bridge instead of returning only text or structured tool data."
  actionability:
    value: 74
    note: "CF can evaluate MCP Apps at the gateway and hosted-service layers, although host capability and iframe security policies remain client decisions."
sources:
  - https://github.com/modelcontextprotocol/ext-apps
  - https://raw.githubusercontent.com/modelcontextprotocol/ext-apps/main/README.md
  - https://github.com/modelcontextprotocol/ext-apps/blob/main/specification/2026-01-26/apps.mdx
  - https://apps.extensions.modelcontextprotocol.io/api/
  - https://github.com/modelcontextprotocol/ext-apps/tree/main/examples
---

## Summary

MCP Apps is the official Model Context Protocol extension and SDK for interactive user
interfaces served by MCP servers. A tool declares a `ui://` resource, a compliant host fetches
and renders the resource in a sandboxed iframe, and a bridge allows the view to receive tool
data or request further tool calls through the host. The extension gives Cloud Foundry-hosted
MCP services a way to deliver charts, forms, dashboards, and other interactive views without
moving all UI logic into the AI client.

## Key findings

- **The protocol adds UI resources to tools.** An MCP tool can declare a `ui://` resource that
  contains its HTML interface. The model calls the tool on the server, then the host fetches
  the associated resource and displays it inline in the conversation.
- **Rendering is host-controlled.** MCP Apps views run in a sandboxed iframe rather than being
  injected directly into the host application. The host decides whether and how to render the
  view, which capabilities to expose, and how to apply its own security and content policies.
- **Communication is bidirectional through a bridge.** The host passes tool results and other
  data to the embedded view using notifications, while the view can invoke tools through the
  host. This supports interactive forms and dashboards rather than a static HTML attachment.
- **The SDK serves three roles.** Packages support app developers building views, host developers
  embedding views, and MCP server authors registering tools and UI metadata. The repository
  includes server helpers, an app bridge, React support, and examples.
- **The official extension does not provide every host.** The repository documents the protocol
  and SDK but notes that it does not contain a supported full host implementation beyond an
  example basic host. Clients may implement their own host or use another compatible framework.
- **Security crosses server, host, and iframe boundaries.** A deployment must control which UI
  resources are trusted, constrain iframe capabilities and network access, validate messages,
  protect host APIs, and re-check authorization when a view invokes a tool. The UI must not be
  treated as a trusted authority merely because it came from an approved MCP server.
- **MCP Apps extends rather than replaces MCP.** Tool discovery, invocation, server identity,
  and authorization remain MCP concerns; MCP Apps adds a standardized interactive presentation
  associated with a tool.
- **Interactive views introduce lifecycle and compatibility questions.** Resource versions,
  host capability negotiation, iframe reloads, tool errors, partial results, and client-specific
  rendering differences all need operational handling beyond a simple text response.

## CF relevance

Cloud Foundry could host MCP servers that expose MCP Apps views for platform operations,
developer workflows, or business tools. A CF-hosted service could keep backend credentials and
policy on the server while returning a chart, approval form, or dashboard resource to a client
through an MCP gateway. Service bindings could provide endpoint and scoped credentials, while
UAA or another identity service authenticates the user or workload behind tool calls.

The gateway and hosting boundary remain important. A CF MCP gateway could apply server/tool
policy, record resource and tool access, and prevent unapproved external servers from being
embedded. Diego could run trusted MCP servers, but the host iframe is controlled by the AI
client rather than CF; network isolation, CSP, resource integrity, and sensitive-data handling
must therefore be enforced across both the server and client. Loggregator-compatible events
could correlate a user session, MCP tool call, UI resource, subsequent view action, and backend
operation.

## Open questions

- Which MCP Apps hosts and iframe capabilities should CF support or certify for platform-facing
  tools?
- How should a CF gateway authorize both the initial tool call and later tool calls initiated
  by the embedded view?
- Where should UI resources be stored, versioned, scanned, and served, and how should tenant
  isolation apply to cached resources?
- What CSP, network egress, origin, and iframe policies are required for multi-tenant hosted
  MCP Apps?
- How should UI resource metadata, tool arguments, user actions, and backend effects be audited
  without logging sensitive content?
- Should CF provide reusable MCP Apps views for platform operations, or leave UI catalogs and
  host compatibility entirely to application teams?
