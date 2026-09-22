---
title: "Mecatl: Cloud-Native Agent Harness with Durable State and Permissions"
author: Ruben Koster (@rkoster)
date: 2026-09-17
tags: [orchestration, durable-execution, authorization, observability-governance]
cf_areas: [uaa, capi, diego, loggregator]
status: draft
ratings:
  platform-impact:
    value: 82
    note: "Mecatl packages agent execution, permissions, durable state, and service boundaries in a form relevant to platform-hosted workloads."
  maturity:
    value: 70
    note: "The project has a substantial open-source implementation and Kubernetes reference runtime, while cross-platform operations still require evaluation."
  novelty:
    value: 70
    note: "Its emphasis on deny-dominant permissions, delegated capabilities, durable attribution, and replaceable execution environments distinguishes it from a simple agent SDK."
  actionability:
    value: 81
    note: "The engine and service APIs provide concrete integration points for CF process lifecycle, bindings, identity, draining, and event observability."
sources:
  - https://github.com/stacklok/mecatl
  - https://raw.githubusercontent.com/stacklok/mecatl/main/README.md
  - https://mecatl.dev/docs/intro
  - https://mecatl.dev/docs/building/cloud-native-harness
  - https://mecatl.dev/docs/building/deployment/mecak8s
  - https://mecatl.dev/docs/building/deployment/grpc-http
---

## Summary

Mecatl is an open-source, provider-agnostic cloud-native agent harness for running production
agent workloads on infrastructure an operator controls. It combines a streaming agent loop
with tools, permissions, hooks, delegation, durable sessions, append-only event logs, and
gRPC/HTTP-SSE clients. Its `mecak8s` reference runtime adds Redis-backed state, Kubernetes
session leases, drain handling, and disposable replicas, making it a useful comparison point
for Cloud Foundry's process lifecycle and platform service boundaries.

## Key findings

- **The loop is independent of the client and execution environment.** Mecatl can run locally,
  remotely with durable external state and event history, or across Kubernetes replicas without
  replacing the core agent loop. Model providers and deployment infrastructure connect through
  explicit interfaces.
- **The runtime includes more than model calls.** Its streaming loop provides tool dispatch,
  compaction, hooks, subagents, and teams, while tools and skills are composed through service
  boundaries that can be embedded or exposed through client APIs.
- **Permissions are first-class runtime state.** Mecatl documents deny-dominant permissions,
  approval flows, secret-scrubbed command environments, durable attribution, and an audit trail.
  This treats the agent's authority as part of execution rather than as an afterthought around
  a model API.
- **Delegation narrows authority.** Delegated runs receive derived capabilities that can only
  narrow at each in-process hop. This is a useful pattern for subagents and teams: a child run
  should not automatically inherit or expand the authority of its parent.
- **Sessions and event history are durable.** Pluggable stores hold durable sessions and
  append-only event logs so work can recover after process replacement. The event record also
  provides a basis for attribution and audit across streaming turns and tool calls.
- **The service boundary is explicit.** Mecatl supports gRPC and HTTP/SSE integration, a
  TypeScript SDK, and `mecatui` for local or remote use. The `engine` can be embedded with
  application-selected model providers, state stores, filesystems, and UI.
- **`mecak8s` is a Kubernetes reference runtime, not the whole engine.** The supplied runtime
  uses Redis for session state and event logs, Kubernetes leases to ensure one writer per
  session, and a drain path for replacing Pods. This separates generic runtime guarantees from
  Kubernetes-specific coordination.
- **Disposable replicas require ownership and draining semantics.** A replica can be replaced
  while durable state and session ownership survive elsewhere. Leases prevent concurrent writers
  from corrupting a session, while draining provides a controlled handoff during deployment or
  failure.
- **Provider credentials and execution infrastructure remain replaceable.** Mecatl does not
  require one model provider or one hosting substrate. Operators select adapters, state stores,
  filesystem behavior, and client surfaces for their deployment.
- **Mecatl is a harness, not a complete platform.** It supplies execution and policy mechanisms,
  but operators still need identity, secret distribution, state-store operations, network
  policy, resource isolation, and observability around the harness.

## CF relevance

Mecatl's generic engine could run as a CF application supervised by Diego, with CAPI managing
application lifecycle and service bindings supplying model providers, Redis, databases, or
other external services. UAA or a workload identity mechanism could establish the authority
under which an agent acts, while Mecatl's deny-dominant permissions and derived capabilities
could constrain tool and subagent operations inside that application.

The Kubernetes-specific `mecak8s` design maps to existing CF concerns around process replacement
and draining. CF would need an equivalent durable session ownership mechanism if multiple app
instances can handle the same session. Diego's desired-state and evacuation behavior could
provide lifecycle signals, but an external durable store and a lease or fencing mechanism would
still be needed to avoid concurrent writers during restage, scaling, crash recovery, or
deployment.

Loggregator could carry correlated session, tool, permission, approval, delegation, and drain
events, while the append-only event log remains the authoritative runtime history selected by
the application. Service bindings should not expose broad provider credentials to every agent;
platform-managed credentials, scoped bindings, secret scrubbing, and explicit audit policy are
needed to preserve Mecatl's authority model in a multi-tenant CF environment.

## Open questions

- Can Mecatl's embedded engine run cleanly as a CF application while preserving durable session
  recovery across Diego process replacement?
- What CF service should provide Redis-like session state, append-only events, leases, and
  fencing, and how should it be provisioned through CAPI or service brokers?
- How should UAA identities, CF instance identities, user delegation, and Mecatl capabilities
  combine without allowing subagents to expand authority?
- Which tool permissions, approval events, credentials, and delegated actions should be
  visible in Loggregator, and which belong only in a protected audit store?
- How should a Mecatl session drain between instances during deploy, scale, crash recovery, or
  provider outage, and what guarantees can CF provide to clients using streaming APIs?
- Should CF provide a Mecatl buildpack/service offering, or only the state, identity, network,
  and lifecycle primitives needed to run the harness?
