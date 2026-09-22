---
title: "A2UI: Declarative Agent-Generated User Interfaces"
author: Ruben Koster (@rkoster)
date: 2026-09-17
tags: [inter-agent-comms, governance, ecosystem-survey]
cf_areas: [capi, uaa]
status: draft
ratings:
  platform-impact:
    value: 70
    note: "A portable agent-to-client UI format could improve agent experiences without allowing agents to ship arbitrary executable UI code."
  maturity:
    value: 55
    note: "A2UI has functional implementations and a v0.9 protocol family, but the project identifies itself as an evolving public preview."
  novelty:
    value: 82
    note: "The trusted-catalog and declarative-data boundary addresses the security and portability problems of generated interactive UI."
  actionability:
    value: 64
    note: "CF-hosted agents could emit A2UI messages, but client catalogs, action authorization, and transport integration remain application concerns."
sources:
  - https://github.com/a2ui-project/a2ui
  - https://raw.githubusercontent.com/a2ui-project/a2ui/main/README.md
  - https://github.com/a2ui-project/a2ui/blob/main/docs/public/concepts/architecture.md
  - https://github.com/a2ui-project/a2ui/tree/main/docs/public
---

## Summary

A2UI is an open-source format and library set that lets agents describe rich user interfaces
as declarative JSON rather than executable code. A client receives the description, resolves
its components against a trusted local catalog, and renders native widgets for its framework.
This separates agent-generated UI intent from client-side implementation and is relevant to
Cloud Foundry as a possible presentation protocol for agents hosted remotely.

## Key findings

- **A2UI separates generation from rendering.** An agent produces an A2UI response, a transport
  carries it to a client, and the client renderer maps abstract components to its own widgets.
  The agent does not need to know whether the client uses Flutter, Angular, Lit, React, or
  another framework.
- **The payload is declarative data, not executable UI code.** Clients maintain catalogs of
  trusted components such as cards, buttons, and text fields. The agent can request composition
  using approved components, reducing the risk of executing arbitrary model-generated code.
- **The data model is designed for incremental updates.** A flat component representation with
  identifiers and references can be generated and updated progressively, supporting responsive
  interfaces as an agent conversation evolves.
- **Actions remain an authorization boundary.** Rendering a button or form does not itself
  grant authority. The client and backend must authenticate the user or agent, validate action
  inputs, and enforce permissions when an interaction invokes a tool or application operation.
- **Transport is separated from the UI format.** The project describes agent-to-client
  delivery through channels such as A2A or AG-UI, while the renderer consumes the A2UI payload.
  This allows the same UI representation to travel through different agent architectures.
- **A2UI has multiple renderer ecosystems.** The repository includes or references renderers
  for different client frameworks, including Flutter-related integrations. Interoperability
  depends on clients agreeing on catalog components and protocol versions.
- **Maturity is still evolving.** The repository describes the project as an early public
  preview, reports a v0.9.1 production release in the v0.9 protocol family, and identifies v1.0
  as a release candidate. Implementations and specification details may change.

## CF relevance

Cloud Foundry-hosted agents could send A2UI descriptions to web or native clients without
embedding a particular UI framework in the agent process. A CF application could generate a
progressive form, approval card, dashboard, or action list, while the client owns rendering,
catalog safety, and user interaction. This fits a platform boundary where CF runs agents and
APIs but does not dictate the client UI stack.

The main CF integration concerns are identity and action routing. A rendered action may invoke a
CF-hosted endpoint, MCP tool, or agent callback, so the client must preserve user/session
context and the backend must re-check authorization rather than trusting the UI description.
UAA or another identity provider could authenticate the user, while the agent identity and
conversation context are carried through a platform gateway. Loggregator-compatible events
could correlate generated UI updates, user actions, agent decisions, and resulting platform
operations.

## Open questions

- Which A2UI component catalogs should CF application and platform clients trust, and how should
  catalogs be versioned and distributed?
- How should action authorization distinguish the human user, the agent, and the CF application
  when an A2UI button invokes a privileged operation?
- Which transports should CF-hosted agents support, and how should reconnects and incremental
  UI updates behave?
- How should sensitive data in UI data models be filtered, logged, cached, and isolated by
  organization or space?
- Would CF benefit from reusable A2UI client components for platform operations, or should this
  remain entirely an application-layer concern?
