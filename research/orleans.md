---
title: "Microsoft Orleans — the Virtual Actor Model Dapr's Actors Building Block Came From"
author: Ruben Koster (@rkoster)
date: 2026-08-10
tags: [runtime-lifecycle, inter-agent-comms, orchestration, ecosystem-survey]
cf_areas: []
status: draft
sources:
  - https://github.com/dotnet/orleans
  - https://learn.microsoft.com/en-us/dotnet/orleans/overview
  - https://learn.microsoft.com/en-us/dotnet/orleans/grains/index
  - https://learn.microsoft.com/en-us/dotnet/orleans/implementation/grain-directory
  - https://learn.microsoft.com/en-us/dotnet/orleans/grains/grain-persistence/index
  - https://learn.microsoft.com/en-us/dotnet/orleans/streaming/index
  - https://learn.microsoft.com/en-us/dotnet/orleans/grains/reentrancy
  - https://learn.microsoft.com/en-us/dotnet/orleans/grains/transactions
  - https://learn.microsoft.com/en-us/dotnet/orleans/host/client
  - https://learn.microsoft.com/en-us/dotnet/orleans/host/silo-lifecycle
  - https://dotnetfoundation.org/projects/project-detail/orleans
  - https://www.nuget.org/packages/Microsoft.Orleans.Journaling
  - https://www.nuget.org/packages/Microsoft.Orleans.DurableJobs
  - https://github.com/managedcode/dotPilot
ratings:
  platform-impact:
    value: 62
    note: 'CF lacks a virtual-actor runtime providing stable logical identities, transparent activation, a distributed directory, per-actor persistence, streams, and cross-actor transactions.'
  maturity:
    value: 92
    note: 'Orleans is a long-running .NET Foundation project proven in Halo cloud services, remains active through v10.2.x, and offers mature clustering, persistence, streaming, transactions, and versioning.'
  novelty:
    value: 28
    note: 'Orleans pioneered the virtual-actor model, but transparent activation and location, actor persistence, and single-threaded grains are now established architecture inherited by systems such as Dapr.'
  actionability:
    value: 52
    note: 'The note suggests comparing grains with durable agent identities, but a CF experiment must first resolve .NET-only coupling, silo membership, storage bindings, and the absence of official agent-framework integration.'

---

## Summary

Microsoft Orleans is a .NET framework (MIT-licensed, .NET Foundation project, created by Microsoft
Research and battle-tested running 343 Industries' Halo 4/5 cloud services) that introduced the
[virtual actor model](https://www.microsoft.com/en-us/research/publication/orleans-distributed-virtual-actors-for-programmability-and-scalability/):
"grains" that are always logically addressable, transparently activated on demand across a
cluster of "silos," and garbage-collected when idle. It is the direct conceptual ancestor of
Dapr's Actors building block — Dapr explicitly adopted Orleans' virtual actor pattern — but
Orleans itself is a considerably richer, in-process, .NET-only runtime rather than a
polyglot sidecar API. As of this research it remains under active development (commits and a
v10.2.x release series landing within the last month), and while a handful of community
projects are wiring it up as a substrate for AI agents, I found no official Microsoft
integration tying it directly into Semantic Kernel or Microsoft Agent Framework.

## Key findings

- **Grains, silos, and the grain directory**: a grain is a virtual actor identified by a stable
  key; it doesn't need to be explicitly created or destroyed — calling any grain ID causes the
  runtime to transparently activate an in-memory instance on some "silo" (an Orleans process/host)
  if one isn't already active. The cluster-wide [grain directory](https://learn.microsoft.com/en-us/dotnet/orleans/implementation/grain-directory)
  is a key→silo-location map; as of Orleans v9.0 it defaults to a strongly-consistent
  distributed hash table (two-phase design based on Virtual Synchrony/Vertical Paxos, with virtual
  nodes for load balancing), replacing the original eventually-consistent version. Each silo caches
  directory lookups locally to avoid a network hop on every call.
- **Single-threaded execution with opt-in reentrancy**: grain activations process one request to
  completion before the next by default — [documented explicitly](https://learn.microsoft.com/en-us/dotnet/orleans/grains/reentrancy)
  as a way to avoid the concurrency bugs of shared-memory actor implementations, at the cost of
  possible deadlock if two grains call each other synchronously. Reentrancy can be enabled
  per-grain-class or per-method to allow interleaved processing when needed. This is a more
  granular concurrency control knob than Dapr actors expose.
- **Grain persistence is a pluggable storage abstraction, not the only path to data**: grains can
  have multiple *named* persistent state objects, each backed by a different storage provider
  (Azure Table/Blob, Cosmos DB, DynamoDB, ADO.NET/SQL, Redis, and — as of a same-day-as-this-research
  commit — Google Cloud Firestore). [Docs are explicit](https://learn.microsoft.com/en-us/dotnet/orleans/grains/grain-persistence/index)
  that Orleans deliberately does *not* try to be a full ORM — it hands storage providers complete
  control over the on-disk format, and grains remain free to talk to databases directly instead.
- **Distributed ACID transactions**: the `Microsoft.Orleans.Transactions` package provides
  [cross-grain distributed transactions](https://learn.microsoft.com/en-us/dotnet/orleans/grains/transactions)
  with ACID semantics against persistent grain state, opt-in on both silo and client. This is a
  capability with no equivalent in Dapr's Actors building block.
- **Streams as a first-class, separate pub/sub layer**: [Orleans Streams](https://learn.microsoft.com/en-us/dotnet/orleans/streaming/index)
  give grains and clients a stream abstraction (identified by `StreamId`) portable across
  Event Hubs, Service Bus, Azure Queues, and Kafka, with durable subscriptions that survive grain
  deactivation — distinct from the newer, simpler `IAsyncEnumerable`-based request/response
  streaming added for single-call use cases.
- **Grain versioning and heterogeneous clusters**: grain interfaces can be optionally versioned;
  the runtime tracks which silo hosts which implementation version and uses that in placement
  decisions, enabling rolling upgrades of stateful services and clusters where different silos
  run different code — a capability aimed squarely at safely evolving long-lived stateful
  systems, which Dapr's actor model doesn't address at this level of granularity.
- **In-process, not sidecar**: an Orleans client is typically *co-hosted in the same process* as
  the silo/grain code — [the docs recommend this](https://learn.microsoft.com/en-us/dotnet/orleans/host/client)
  for lower latency and simpler deployment, explicitly trading away process isolation between
  client and grain code. This is the opposite tradeoff from Dapr's sidecar model, where the actor
  runtime is isolated in `daprd` and reached over local HTTP/gRPC from any language.
- **Precise comparison with Dapr Actors**: Dapr's actor runtime borrows the core idea — turn-based
  single-threaded execution per actor, transparent activation/deactivation, idle GC — but is
  reachable from *any language* via the sidecar's HTTP/gRPC API, and its actor placement service
  is a separate, simpler component than Orleans' strongly-consistent directory. What Orleans has
  that Dapr's actors don't: opt-in reentrancy control, distributed ACID transactions, a
  first-class streams subsystem, grain interface versioning for heterogeneous/rolling-upgrade
  clusters, and (being a library, not an API surface) compile-time-checked, strongly-typed grain
  interfaces with generated proxies rather than string-keyed HTTP calls. What Dapr's actors have
  that Orleans doesn't: polyglot reach (an actor can be called from a Python or Go app without a
  .NET client), and integration with Dapr's other building blocks (pub/sub, state, workflow) as
  siblings behind the same sidecar rather than separate subsystems to wire up.
- **License and governance**: MIT-licensed, [.NET Foundation project](https://dotnetfoundation.org/projects/project-detail/orleans),
  10.8k GitHub stars. Actively developed: the latest commit at the time of this research (Aug 10,
  2026) landed the same day, and the release history shows a steady v10.2.x cadence (v10.2.2 in
  late July 2026, minor releases roughly monthly). Top contributors (Reuben Bond, Sergey Bykov,
  Gabriel Kliot, and others) are Microsoft engineers.
- **Relationship to Semantic Kernel and Microsoft Agent Framework**: these are separate
  Microsoft/`.NET` ecosystem projects. I found no official package or documentation connecting
  Orleans to Semantic Kernel or to Microsoft Agent Framework as a shared runtime — MAF's own
  durable-workflow story is built on Azure Durable Task Framework, not Orleans (see
  `microsoft-agent-framework.md`). The connection appears to be "same broad ecosystem, built by
  overlapping Microsoft teams," not shared infrastructure — worth treating as separate projects
  unless further evidence emerges.
- **New, not-yet-stable infrastructure that's plausibly agent-relevant**: two prerelease packages
  stood out — `Microsoft.Orleans.Journaling` (currently `10.2.2-rc.2.alpha.1` on NuGet), which
  persists durable state changes as an ordered, replayable journal (JSON-Lines format) rather than
  full-state snapshots — a pattern well-suited to append-only conversation/memory logs; and
  `Microsoft.Orleans.DurableJobs` (369K+ downloads despite prerelease status), a distributed
  one-time-job scheduler (as opposed to Orleans' existing recurring-task Reminders) with
  automatic retries and rebalancing across silos. Neither is marketed as "for AI agents" in its
  own docs — I'm inferring the fit from the shape of the problem they solve, not from a vendor
  claim.
- **Concrete (community, not official) AI-agent adoption**: a GitHub search turned up several
  small third-party projects explicitly combining Orleans with agent workloads — e.g.
  [`managedcode/dotPilot`](https://github.com/managedcode/dotPilot) (embeds an Orleans host
  inside a desktop app specifically for state, alongside Microsoft Agent Framework for
  orchestration), `aevatarAI/AISmart` ("AI Agent Framework based on ABP + Orleans"), and other
  low-star repos describing themselves as "durable, distributed AI agent runtime on .NET +
  Orleans." None of these are official Microsoft projects, and star counts are low (single/low
  double digits) — this reads as early, exploratory community interest rather than an
  established pattern.
- **.NET-only, no way around it**: both the silo (host) and client must be .NET processes; there
  is no sidecar, HTTP gateway, or officially supported non-.NET client analogous to how Dapr or
  Temporal support polyglot callers. Adopting Orleans means committing the relevant service(s) to
  .NET end to end.

## CF relevance

Orleans is a useful reference point precisely because it's the design Dapr's Actors building
block copied from — comparing the two clarifies which actor-model guarantees CF would inherit
"for free" if it leaned on Dapr's actors versus which ones (transactions, streams, reentrancy
control, versioned rolling upgrades) only exist in the fuller Orleans implementation and would
have to be reinvented or done without. The strongly-consistent grain directory and
silo-membership/placement machinery are also a good comparison point for how CF's own instance
placement (Diego) differs from a peer-to-peer, self-hosted cluster model. Given the .NET-only
constraint, Orleans itself is unlikely to be directly adoptable in a polyglot CF context, but the
architectural patterns (virtual activation, idle GC, versioned rolling upgrades) may still be
worth studying even where Orleans itself isn't.

## Open questions

- Is the "grains as durable agent state" pattern (journaling, per-agent grain = per-conversation
  actor) more than a few early community experiments, or is there a more established design
  pattern emerging that we should track over time?
- Given Orleans' in-process/co-hosted client model, how would its trust/isolation story compare
  to CF's process-per-app-instance isolation if grains ever needed to run "someone else's" agent
  code?
- Does the .NET-only constraint make Orleans irrelevant for a polyglot CF agent runtime, or is
  there value in extracting its virtual-actor *design* independent of the .NET implementation?
- Would it be worth a closer look at `Microsoft.Orleans.DurableJobs` and `Microsoft.Orleans.Journaling`
  once they leave prerelease, given how directly the "durable one-time job" and "replayable
  journal" shapes map onto agent task scheduling and conversation memory?
