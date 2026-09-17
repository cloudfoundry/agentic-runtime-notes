---
title: "WebMCP: Browser-Native Tools for Agent Interaction"
author: Ruben Koster (@rkoster)
date: 2026-09-17
tags: [inter-agent-comms, governance, ecosystem-survey]
cf_areas: [capi, uaa]
status: draft
ratings:
  platform-impact:
    value: 70
    note: "Web applications could expose agent-friendly actions without every platform team building a separate backend integration."
  maturity:
    value: 42
    note: "WebMCP is an evolving proposal with implementation-status and browser-support questions still visible in the project."
  novelty:
    value: 84
    note: "It places the tool boundary inside the browser page, preserving user session context instead of requiring a separate server-side integration."
  actionability:
    value: 65
    note: "CF application teams can evaluate the pattern, but platform guidance depends on browser support, consent, and web security behavior."
sources:
  - https://github.com/webmachinelearning/webmcp
  - https://raw.githubusercontent.com/webmachinelearning/webmcp/main/README.md
  - https://github.com/webmachinelearning/webmcp/blob/main/declarative-api-explainer.md
  - https://github.com/webmachinelearning/webmcp/blob/main/implementation-status.md
  - https://developer.chrome.com/docs/ai/webmcp/secure-tools
---

## Summary

WebMCP is an evolving browser-oriented proposal for exposing web application functionality as
tools that AI agents can discover and invoke. Pages can define tools imperatively with
JavaScript or declaratively through HTML forms, allowing the browser, page, user, and agent to
share the existing UI and session context. This differs from a backend MCP integration, where
an agent platform calls a separate service and the developer must reproduce application state
and authentication there.

## Key findings

- **Tools live in the page context.** WebMCP is intended to expose functionality already
  implemented by a web application, including actions that would otherwise require simulated
  clicks, DOM inspection, or screenshots.
- **The API has imperative and declarative paths.** JavaScript can register richer tools for
  functionality that is not representable as a form, while standard HTML forms can provide a
  declarative counterpart with structured inputs.
- **Browser context is the main differentiator.** The page can retain its current UI state,
  user session, and application-specific behavior, reducing the need to replicate those
  concerns in a separate agent-facing backend.
- **WebMCP complements rather than replaces browser automation.** If a page does not expose a
  suitable tool, an agent or assistive technology can still fall back to ordinary browser
  automation techniques.
- **The tool surface needs security design.** Exposing a JavaScript function as an agent tool
  does not remove authorization, consent, input validation, CSRF, sensitive-action confirmation,
  or output-data concerns. Web developers remain responsible for designing safe tool behavior.
- **The project is not the same boundary as server-side MCP.** WebMCP is a client-side/browser
  integration, while MCP servers expose capabilities through backend services. A product may
  use both: server-side tools for durable backend operations and WebMCP for actions requiring
  the active browser context.
- **Implementation maturity matters.** The repository labels WebMCP as experimental/evolving
  and provides implementation-status material. Browser availability and agent support should
  be checked before treating it as a portable production dependency.

## CF relevance

WebMCP could let a CF-hosted web application expose agent actions without asking the platform
team to deploy a second MCP backend that reconstructs the application's session and auth
context. A CF application could continue to own its routes, UAA-backed login, CSRF policy, and
business authorization while exposing a deliberately narrow browser tool surface.

This is complementary to a CF AI gateway. A gateway can govern model and server-side MCP
traffic, while WebMCP keeps user-mediated browser interactions local to the application. The
platform would need guidance for how browser agents identify themselves, how user consent is
collected, how tools inherit or constrain session authority, and how WebMCP actions appear in
application audit logs and Loggregator streams.

## Open questions

- Which browsers and agent clients will support WebMCP, and what fallback should applications
  provide when it is unavailable?
- How should a WebMCP tool distinguish user authority from agent authority within the same
  browser session?
- Which actions require explicit user confirmation, and how should applications prevent CSRF or
  confused-deputy behavior?
- Should CF publish secure WebMCP guidance or libraries for UAA sessions, route protection, and
  audit correlation?
- How should WebMCP actions be correlated with model requests, agent identities, and platform
  logs without leaking sensitive page state?
