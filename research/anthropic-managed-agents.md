---
title: "Anthropic Managed Agents — Remote Hands Architecture"
author: Ruben Koster (@rkoster)
date: 2026-07-02
tags: [runtime-lifecycle, sandboxing-isolation, identity]
status: draft
sources:
  - https://www.anthropic.com/engineering/managed-agents
ratings:
  platform-impact:
    value: 75
    note: 'Stateless CF app processes map to the brain, but CF lacks on-demand sandbox hands, an external append-only agent session service, and credential proxies that keep secrets out of generated-code environments.'
  maturity:
    value: 62
    note: 'Anthropic reports operating the architecture and measured p50 TTFT improvements of about 60% and p95 improvements over 90%, but publishes neither a specification nor an open implementation for its session interface.'
  novelty:
    value: 72
    note: 'The independently scalable brain, replaceable hands, and external positional event log form an emerging decomposition, strengthened by vault-backed proxies that structurally exclude credentials from both harness and sandbox.'
  actionability:
    value: 78
    note: 'CF can prototype a stateless brain app against a durable event service and on-demand sandbox, then route one service credential through a proxy instead of injecting it into the sandbox.'

---

## Summary

Anthropic's Managed Agents service introduces a "remote hands" architecture that decouples
three concerns into independent, replaceable components: the **brain** (stateless
orchestration harness), the **hands** (on-demand sandboxes and tools), and the **session**
(a durable append-only event log that lives outside the LLM context window). Each
component exposes a minimal interface; none makes assumptions about the others'
implementation.

## Key findings

- **Three clean abstractions**: Brain — a stateless loop that calls the LLM and routes
  tool calls; can crash and resume via `wake(sessionId)`. Hands — tools with a single
  interface (`execute(name, input) → string`); could be a container, a phone, or any other
  executor. Session — an append-only event log (`emitEvent`, `getEvents`) that stores
  everything that happened outside the LLM context window, enabling rewind and context
  replay.
- **Structural credential isolation**: In the coupled design, untrusted generated code ran
  in the same container as credentials — a prompt injection only needed to convince the LLM
  to read its own environment. The fix is structural: credentials never reach the sandbox.
  Git tokens are wired into the local git remote at sandbox init and never handled by the
  agent. MCP OAuth tokens live in a secure vault; a dedicated proxy fetches them on behalf
  of tool calls so the harness never sees them.
- **On-demand provisioning cuts TTFT**: Containers are provisioned via tool call
  (`provision({resources})`), not upfront before the session starts. Inference begins as
  soon as the harness pulls pending events from the session log. This dropped p50 TTFT by
  ~60% and p95 by over 90%.
- **Many brains, many hands**: Stateless harnesses scale independently and connect to
  hands only when needed. Multiple execution environments can be active simultaneously —
  Claude reasons about which hand to use for each tool call. Brains can pass hand
  references to each other with no coupling between them.
- **Session as external durable log**: The session is not in-process state and not part of
  the LLM context window. It is a positional event stream the harness queries selectively.
  This separates durable context storage (what happened) from context management strategy
  (what to send to the LLM) — the harness can transform, summarize, or filter events
  before passing them as context.

## CF relevance

The brain/hands/session decomposition is a reference model for how a platform could
structure agent workloads without coupling orchestration to execution. The stateless brain
maps naturally to a horizontally scalable app process; the hands map to on-demand
provisioned sandboxes; the session maps to an external durable service. The structural
credential isolation pattern — credentials routed through a proxy, never injected into the
execution environment — is a concrete answer to the "how do agents get secrets without
exposing them to generated code" problem.

## Open questions

- The session interface (`emitEvent`, `getEvents`) is described conceptually — is there a
  published spec or open-source implementation, or is this proprietary to Anthropic's
  service?
- How does the credential proxy pattern interact with short-lived tokens (OAuth access
  tokens that expire mid-session) — does the proxy handle refresh, or does the harness
  coordinate that?
- The "many brains" model assumes stateless harnesses — what is the recommended approach
  for harness state that genuinely can't be externalized (e.g., in-memory caches, loaded
  model weights)?
- How does the `provision({resources})` interface handle quota enforcement and
  multi-tenancy in practice?
