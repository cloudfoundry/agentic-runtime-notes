---
title: "Reactive Agents: Infinity/RAP and MCP Asynchronous Extensions"
author: Ruben Koster (@rkoster)
date: 2026-09-17
tags: [orchestration, durable-execution, inter-agent-comms, event-driven, runtime-lifecycle, ecosystem-survey]
cf_areas: [capi, diego, loggregator]
status: draft
ratings:
  platform-impact:
    value: 82
    note: "Asynchronous tasks and event-driven wake-ups could make long-running agents a first-class workload for Cloud Foundry, but require platform-managed messaging and durable state."
  maturity:
    value: 58
    note: "Infinity has a concrete runtime and RAP specification, MCP Tasks has a stable schema snapshot, while MCP Triggers & Events remains explicitly experimental."
  novelty:
    value: 65
    note: "The execution-slice model composes established hibernation and wake-up patterns with protocol-level callbacks, subscriptions, and durable task state rather than inventing those lifecycle patterns."
  actionability:
    value: 76
    note: "The patterns identify concrete CF integration points around queues, state, callbacks, ordering, and observability, even though no direct CF integration is documented."
sources:
  - https://github.com/hydro-project/infinity
  - https://infinity.hydro.run/docs/infinity-runtime/overview
  - https://infinity.hydro.run/docs/infinity-runtime/architecture
  - https://infinity.hydro.run/docs/rap/what-is-rap
  - https://infinity.hydro.run/docs/rap/spec/overview
  - https://infinity.hydro.run/docs/infinity-runtime/deploying-on-lambda
  - https://github.com/modelcontextprotocol/ext-tasks
  - https://github.com/modelcontextprotocol/experimental-ext-triggers-events
  - https://raw.githubusercontent.com/modelcontextprotocol/experimental-ext-triggers-events/main/docs/design-sketch-proposal.md
---

## Summary

Infinity is a Rust framework for highly concurrent agents and the reference runtime for the
Reactive Agent Protocol (RAP). It models work as short execution slices: load durable state,
process a message and model completion, dispatch an asynchronous tool call, persist state,
and yield. MCP Tasks provides an official MCP extension for durable call-now/fetch-later task
state, while the explicitly experimental Triggers & Events work explores proactive server
notifications. Together, these projects show several complementary ways to make long-running
and event-driven agent work possible without holding an agent process open.

## Key findings

- **Infinity makes every wake-up a message.** Its `InputMessage` covers user text, tool
  results, subscription events, child-thread reports, OAuth challenges, and timer wake-ups.
  A `group_id` identifies the conversation thread, allowing the runtime to use one message
  processing model for interactive and externally triggered work.
- **Execution happens in non-blocking slices.** A slice restores conversation history and
  processed-message state, deduplicates inputs, runs a model completion, dispatches a tool
  call, persists the remaining state, and ends without waiting for external work. The next
  message reconstructs the state needed for continuation.
- **RAP uses an asynchronous callback contract.** The runtime sends a tool invocation over
  HTTP with a callback URL. The tool acknowledges immediately, and later posts a result or
  event to the callback. That callback is consumed as a new wake-up message rather than as a
  response on the original connection.
- **Waiting is a first-class agent behavior.** RAP supports long-running calls,
  subscriptions, webhooks, human approvals, and hibernating agents. When no work is pending,
  the agent process can shut down and resume when a user message, tool result, subscription
  event, or timer message arrives.
- **Durability does not imply exactly-once execution.** Infinity documents per-thread
  ordering, durable state, and deduplication of processed message IDs for infrastructure with
  at-least-once delivery. Redelivery, restarts, and cold starts are expected conditions, so
  applications still need idempotent effects and clear retry behavior.
- **MCP Tasks standardizes deferred task retrieval.** The official `io.modelcontextprotocol/tasks`
  extension describes tasks as durable state machines with receiver-generated task IDs. It
  supports call-now/fetch-later workflows such as expensive computation, batch processing,
  and external jobs. Its repository identifies the `2026-07-28` schema directory as a stable
  snapshot and bases the extension on SEP-2663.
- **MCP Tasks and RAP emphasize different boundaries.** MCP Tasks adds task lifecycle state,
  status inspection, polling, and deferred result retrieval to MCP. RAP defines a fire-and-
  forget tool invocation and callback path designed for a runtime that can hibernate. A task
  can be used by a reactive runtime, but the two concepts are not interchangeable.
- **Triggers & Events explores proactive delivery.** The MCP Triggers & Events repository is
  explicitly an experimental incubation space, not an official MCP specification or
  recommendation. Its working group is exploring event discovery, poll and stream delivery,
  webhook callbacks, subscription TTLs, opaque cursors and replay, event IDs for deduplication,
  webhook signatures, and ordering guarantees across transports.
- **The experimental event design complements task state.** Tasks answer "what is the status
  of this deferred operation and when can I fetch its result?" Events answer "how does a client
  learn that something happened without polling or holding a stream open?" A reactive agent
  may need both, but the delivery, authorization, retention, and replay policies differ.
- **MCP remains useful for fast tools.** Infinity can run MCP servers through a compatibility
  layer. RAP changes the waiting contract for tools, MCP Tasks adds a durable task lifecycle,
  and Triggers & Events explores server-initiated event delivery; none is a replacement for
  all of the existing MCP tool ecosystem.
- **Infinity has a concrete serverless deployment model.** Its Lambda architecture maps one
  execution slice to a short-lived invocation, uses SQS FIFO for ordered input, Aurora DSQL
  for durable state, Bedrock for model calls, and a receiver Lambda for RAP callbacks. This
  demonstrates one implementation of the pattern, not an existing Cloud Foundry integration.
- **The scope is agent/tool interaction.** Infinity, RAP, and the MCP extensions address
  asynchronous execution and communication. They do not provide general model-provider
  routing, application ingress, or every workflow orchestration capability a platform may
  need.

## CF relevance

Cloud Foundry can run a resident Infinity process or another RAP-compatible service as an
application, with CAPI managing application metadata and Diego supervising the process. That
deployment would not automatically provide hibernation or scale-to-zero: ordinary CF routing
delivers incoming HTTP traffic to running instances, while a reactive runtime needs an event or
message to activate work after the process has stopped.

A platform implementation would likely need an external or CF-managed queue and durable state
store for wake-ups, per-thread ordering, deduplication, task state, subscriptions, and timers.
A callback or event receiver could translate RAP callbacks, MCP task completions, and MCP event
webhooks into queue messages. Service bindings could expose those endpoints and credentials to
applications, while platform policy controls callback authentication, tenant routing, retry
limits, replay, and isolation between spaces.

The model also changes observability requirements. Loggregator-compatible logs and metrics
would need to correlate one logical agent turn across multiple short-lived processes, model
calls, tool callbacks, retries, polling, and external events. If the platform exposes a common
reactive-agent substrate, it would need to make delivery guarantees and failure semantics
visible to operators rather than hide them behind an apparently synchronous application API.
The most direct CF opportunity may therefore be a durable event and activation service that
supports multiple runtimes and protocols, rather than choosing Infinity, RAP, MCP Tasks, or
Triggers & Events as the sole platform abstraction.

## Open questions

- Should Cloud Foundry provide a common durable input and event substrate for reactive agents,
  or should teams provision queues and state stores themselves?
- Should a CF platform offering expose RAP, MCP Tasks, MCP Triggers & Events, or an
  implementation-neutral abstraction over tasks, callbacks, and subscriptions?
- How should callback and webhook authentication, tenant routing, subscription ownership, and
  cross-space isolation work?
- Which delivery, ordering, deduplication, replay, and retry guarantees should the platform
  expose, and how should applications declare idempotency requirements?
- Should CF support message-triggered scale-to-zero activation, or focus on resident processes
  and let an external serverless substrate provide hibernation?
- How should task state, event subscriptions, durable cursors, state stores, and timers be
  provisioned and billed?
- How should asynchronous agent activity appear in Loggregator, tracing, usage accounting, and
  operator-facing failure events?
- Can RAP be adopted independently of Infinity's Rust runtime, and can the MCP extensions
  converge with reactive-agent implementations without fragmenting the tool ecosystem?
