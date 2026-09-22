---
title: "Agent Substrate: Multiplexed Sandboxed Actors"
author: Ruben Koster (@rkoster)
date: 2026-09-17
tags: [sandboxing, workload-isolation, orchestration, ecosystem-survey]
cf_areas: [diego, capi]
status: draft
ratings:
  platform-impact:
    value: 86
    note: "The actor/worker model targets the density and isolation problems that become important when every agent needs its own stateful sandbox."
  maturity:
    value: 55
    note: "The repository has a working counter demonstration and substantial components, but its architecture document explicitly marks much of the design as aspirational."
  novelty:
    value: 84
    note: "Substrate combines sandbox checkpoint/restore, pre-started workers, actor teleportation, and traffic routing into an agent-oriented execution substrate."
  actionability:
    value: 70
    note: "The architecture provides concrete questions for CF around Diego density, snapshots, isolation, and route-triggered activation, although no CF integration is provided."
sources:
  - https://github.com/agent-substrate/substrate
  - https://raw.githubusercontent.com/agent-substrate/substrate/main/README.md
  - https://raw.githubusercontent.com/agent-substrate/substrate/main/docs/architecture.md
  - https://github.com/agent-substrate/substrate#tour
  - https://raw.githubusercontent.com/agent-substrate/substrate/main/demos/counter/README.md
---

## Summary

Agent Substrate is a Kubernetes-backed execution system for running large numbers of
stateful, mostly-idle actors in isolated sandboxes. It separates an actor's lifecycle from
the worker that currently hosts it: actors can be suspended, snapshotted, moved to a ready
worker, and resumed when traffic arrives. The project is infrastructure rather than an agent
SDK, and its architecture documentation explicitly identifies substantial parts of the design
as aspirational.

## Key findings

- **The central abstraction is actor versus worker.** An actor is an instance of an
  agent-like workload, not necessarily an AI agent. Substrate maps many actors onto a smaller
  pool of ready workers, relying on the fact that these workloads spend much of their time
  waiting for input or events.
- **Lifecycle is independent of worker placement.** The control plane manages actor creation
  and destruction, suspension and resumption, worker assignment, and traffic routing. A
  suspended actor can be resumed on any suitable worker instead of remaining tied to the
  process or node where it last ran.
- **Pre-started workers target both density and latency.** Rather than waiting for the
  Kubernetes scheduler on every activation, Substrate keeps worker Pods ready and assigns an
  actor to one when an event arrives. This allows oversubscription while aiming for sub-second
  resume operations.
- **State can include volatile process memory.** The counter demo shows a `Full`-scope snapshot
  preserving process memory together with filesystem state across suspend and resume. A
  `Data`-scope policy preserves durable-volume data but restarts in-memory state, making the
  snapshot policy an explicit application and platform trade-off.
- **The implementation is split into focused components.** `ateapi` exposes gRPC lifecycle
  operations for actors and workers; `atelet` supervises worker Pods and coordinates snapshots
  and state transfers; `atecontroller` reconciles WorkerPool custom resources; and `atenet`
  provides Envoy routing and proxy sidecars. Separate helpers integrate gVisor checkpoint and
  restore or run actors inside cloud-hypervisor microVMs.
- **Kubernetes is the infrastructure substrate.** Substrate uses Kubernetes for provisioning,
  worker lifecycle management, Pod autoscaling, and controller integration, while adding
  agent-specific scheduling and lifecycle control above those primitives. The counter demo
  uses a WorkerPool CRD and an Agent Substrate actor template managed through an atespace.
- **Security is part of the execution model.** The project targets untrusted workloads and
  supports sandbox technologies such as gVisor and microVMs. The README describes zero-trust
  kernel and network isolation as design goals, but the exact security boundary and operational
  guarantees require further investigation.
- **The evidence has different maturity levels.** The repository includes a runnable counter
  demo that preserves state across suspend/resume. In contrast, the architecture document
  states that much of its described architecture is aspirational, so performance and scale
  claims should be treated as project targets or demonstrations until backed by reproducible
  benchmark evidence.
- **This is not an agent programming framework.** Substrate supplies lifecycle, placement,
  isolation, state preservation, and routing infrastructure. Agent logic, model access, tools,
  and application-level durable workflows remain the responsibility of the workload or other
  platform components.
- **The project has an explicit support caveat.** The README states that Agent Substrate is
  not an officially supported Google product. That governance and support status matters when
  evaluating it as a platform dependency.

## CF relevance

Agent Substrate is a useful comparison point for Cloud Foundry because it attacks a problem
that ordinary application scaling does not fully solve: many isolated workloads are idle most
of the time, but resuming them quickly requires preserving state and avoiding a fresh
scheduler placement on every request. Diego already owns process placement and health
management, while CAPI owns application lifecycle and metadata. A Substrate-like layer could
sit beside those systems or extend them with actor identity, suspended state, worker pools, and
route-triggered activation.

The mapping is not direct. CF applications are normally long-running processes with routing
to currently running instances; Substrate assumes actors can disappear from workers while
retaining execution state. Implementing that model in CF would require trusted checkpoint and
restore support, durable snapshot storage, stable network identity, route lookup during resume,
and clear semantics for in-flight requests. It would also need an isolation boundary comparable
to the selected gVisor or microVM backend rather than relying only on ordinary application
process isolation.

The most relevant research question is whether actor multiplexing belongs inside Diego or in an
adjacent substrate that Diego manages as a specialized workload. Either option would need
Loggregator-compatible lifecycle and routing events, resource accounting per suspended actor,
snapshot failure visibility, and tenant-aware network policy. The counter demo's distinction
between process-memory snapshots and durable-volume snapshots is especially relevant to CF's
stateful-agent discussions: preserving memory can improve resume fidelity, but increases the
security, storage, compatibility, and failure-recovery burden.

## Open questions

- Could Diego support suspended actor identities and fast resume, or should CF expose a
  separate actor substrate alongside ordinary applications?
- What checkpoint format, storage backend, encryption, and key lifecycle would be trusted for
  process memory containing credentials or sensitive agent context?
- How should CF route a request to a suspended actor, and what happens to requests that arrive
  while snapshot restore or worker assignment is failing?
- Which isolation guarantees are required for untrusted agent code, and can they be provided by
  the existing Diego execution model or only by gVisor/microVM-style workers?
- How should suspended actors consume quota, memory, storage, network identity, and billing
  resources while they are not attached to a worker?
- What lifecycle, snapshot, resume, and routing events should Loggregator expose to operators?
- Which parts of Agent Substrate are validated by the current demo and benchmarks, and which
  remain aspirational before it is suitable as a production platform dependency?
