---
title: "Agent2Agent (A2A) Protocol — Agent-to-Agent Interoperability"
author: Ruben Koster (@rkoster)
date: 2026-07-02
tags: [inter-agent-comms, ecosystem-survey]
cf_areas: [capi, uaa]
status: draft
sources:
  - https://a2a-protocol.org/latest/
  - https://github.com/a2aproject/A2A
---

## Summary

Agent2Agent (A2A) is a Linux Foundation open standard (originated at Google) for AI agent
communication. It defines Agent Cards for capability discovery and Tasks as the core
delegation primitive, with no central registry required. It is designed to complement MCP:
MCP connects agents to tools, A2A connects agents to agents.

## Key findings

- **Agent Card**: Self-discoverable JSON document describing an agent's capabilities, skills,
  supported formats, and endpoints — how agents advertise themselves to the world.
- **Tasks**: Core communication abstraction with `id`, `status`, `history`, and `artifacts`.
  Supports streaming and async operations.
- **Decentralized discovery**: Client agents discover remote agents via Agent Card — no
  central registry required.
- **Enterprise features**: Built-in authentication, authorization, task delegation with
  context preservation, and an extensions mechanism for custom behavior.
- **MCP/A2A complementary**: MCP handles agent-to-tool communication; A2A handles
  agent-to-agent coordination. Both are needed for a full multi-agent system.

## CF relevance

If agents are first-class workloads on a platform, they need a standard way to discover and
call each other — analogous to how HTTP serves traditional web services. A2A's Agent Card
model raises questions about where capability discovery lives on a platform: route metadata,
a service registry, or a dedicated agent registry. A2A's task delegation model also implies
stateful, potentially long-running calls, which intersects with how platforms handle async
work and routing.

## Open questions

- How do agents discover each other within a bounded deployment (e.g., an org or space)?
- Should A2A be a natively supported protocol alongside HTTP, or an application-level concern?
- How to handle authentication between agents with different trust boundaries?
- What's the right scope for an "agent registry" — per-space, per-org, global?
