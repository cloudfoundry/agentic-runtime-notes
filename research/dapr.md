---
title: "Dapr — Distributed Application Runtime"
author: Ruben Koster (@rkoster)
date: 2026-08-10
tags: [runtime-lifecycle, inter-agent-comms, identity, orchestration, ecosystem-survey]
cf_areas: []
status: draft
sources:
  - https://dapr.io/
  - https://docs.dapr.io/overview/
  - https://docs.dapr.io/developing-applications/building-blocks/
  - https://docs.dapr.io/concepts/dapr-services/sidecar/
  - https://docs.dapr.io/operations/security/mtls/
  - https://docs.dapr.io/developing-applications/building-blocks/workflow/workflow-overview/
  - https://docs.dapr.io/developing-ai/dapr-agents/dapr-agents-introduction/
ratings:
  platform-impact:
    value: 78
    note: 'Initial review of Dapr — Distributed Application Runtime: its subject and tags indicate how broadly the capability could affect an agentic platform.'
  maturity:
    value: 76
    note: 'Initial review of Dapr — Distributed Application Runtime: this score reflects the amount of established external practice visible in the note.'
  novelty:
    value: 62
    note: 'Initial review of Dapr — Distributed Application Runtime: this score reflects how distinct or emerging the approach appears in the current landscape.'
  actionability:
    value: 66
    note: 'Initial review of Dapr — Distributed Application Runtime: this score reflects how readily the material could guide a focused experiment or follow-up.'

---

## Summary

Dapr (Distributed Application Runtime) is a [CNCF graduated project](https://www.cncf.io/projects) that
provides a set of language-agnostic HTTP/gRPC APIs — "building blocks" — for common distributed-systems
concerns (service invocation, pub/sub, state, actors, workflow, bindings, secrets), exposed via a sidecar
process rather than an in-process SDK. It decouples application code from infrastructure through pluggable
components, and is increasingly marketed by its maintainers not just as a microservices runtime but as a
"durable execution engine for workflows and AI agents" — i.e. infrastructure for building resilient,
crash-recoverable agentic systems.

## Key findings

- **Sidecar, not a library**: the Dapr APIs run in a separate process (`daprd`) alongside the app and are
  called over local HTTP or gRPC — the app never links Dapr runtime code directly. On Kubernetes,
  `dapr-sidecar-injector` watches for the `dapr.io/enabled` pod annotation and injects `daprd` as a
  container in the same pod (or as a [native Kubernetes 1.28+ sidecar container](https://docs.dapr.io/concepts/dapr-services/sidecar/)); in self-hosted mode the CLI (`dapr run`) launches `daprd` next to the app binary.
- **Eleven building-block APIs**: [service invocation](https://docs.dapr.io/developing-applications/building-blocks/service-invocation/), [pub/sub](https://docs.dapr.io/developing-applications/building-blocks/pubsub/), [state management](https://docs.dapr.io/developing-applications/building-blocks/state-management/),
  [bindings](https://docs.dapr.io/developing-applications/building-blocks/bindings/), [actors](https://docs.dapr.io/developing-applications/building-blocks/actors/), [workflow](https://docs.dapr.io/developing-applications/building-blocks/workflow/), [secrets](https://docs.dapr.io/developing-applications/building-blocks/secrets/),
  [configuration](https://docs.dapr.io/developing-applications/building-blocks/configuration/), [distributed lock](https://docs.dapr.io/developing-applications/building-blocks/distributed-lock/), [cryptography](https://docs.dapr.io/developing-applications/building-blocks/cryptography/), and [jobs](https://docs.dapr.io/developing-applications/building-blocks/jobs/)
  — each is independently adoptable, so an app can use only pub/sub without pulling in the rest.
- **Pluggable components**: state stores, pub/sub brokers, and bindings are backed by a component
  abstraction — e.g. the state store can be Redis, PostgreSQL, Azure Cosmos DB, DynamoDB, etc.,
  swapped via YAML config with no application code change, similar in spirit to a service-broker/binding
  model.
- **Control plane and mTLS**: a small set of control-plane services — `dapr-operator` (component
  notifications), `dapr-placement-server` (actor placement), `dapr-sentry` (certificate authority), and
  `dapr-scheduler-server` (jobs/reminders scheduling) — support the data-plane sidecars. `dapr-sentry` acts
  as a CA issuing short-lived workload certificates (Ed25519 as of Dapr 1.18) for mutual TLS between
  sidecars, and explicitly provides workload identity via [SPIFFE](https://spiffe.io/).
- **Virtual actors**: Dapr's actor runtime implements the [virtual actor pattern](https://docs.dapr.io/developing-applications/building-blocks/actors/actors-overview/) — single-threaded,
  turn-based execution per actor instance, with the runtime handling activation/deactivation, state, and
  timers/reminders. Actors are garbage-collected when idle, giving a lightweight per-entity concurrency
  model without the app managing locks itself.
- **Workflow as a durable execution engine**: the [workflow building block](https://docs.dapr.io/developing-applications/building-blocks/workflow/workflow-overview/) provides a code-first
  orchestration engine (activities, child workflows, multi-app workflows) where every step is persisted so
  execution can resume from exactly where it left off after a crash or restart; execution histories can
  optionally be [cryptographically signed and verified](https://docs.dapr.io/developing-applications/building-blocks/workflow/workflow-history-signing/) for tamper-evidence.
- **Explicit agentic positioning**: Dapr's own docs now describe it primarily as "the durable execution
  engine for workflows and AI agents." [Dapr Agents](https://docs.dapr.io/developing-ai/dapr-agents/dapr-agents-introduction/) (a separate framework, own note pending) builds on
  this by giving each agent a cryptographic identity and backing agent/tool-call loops with the same
  durable workflow engine, so an agent can crash and resume mid-task without losing progress — this is
  covered in more depth in `research/dapr-agents.md`.

## CF relevance

Dapr's sidecar-plus-pluggable-component model is conceptually close to CF's app + service-binding pattern,
but pushed further: instead of just wiring credentials to an app, Dapr standardizes the *API surface* an
app talks to (pub/sub, state, secrets) and lets the operator swap the backing implementation transparently.
The mTLS-via-CA-issued-workload-certs-with-SPIFFE-identity model is also a natural point of comparison with
however CF chooses to do inter-app/inter-agent identity and transport security. Not sure yet whether the
right analogy is "Dapr building blocks as CF service types" or something closer to the CF runtime's own
process-to-process trust model — worth raising as an open comparison rather than a settled mapping.

## Open questions

- Does a CF-hosted agent runtime want app-level building-block APIs (state, pub/sub) as a platform
  primitive, or should that remain squarely in "bring your own service broker" territory?
- How would Dapr's sidecar injection and per-app control-plane footprint (placement, sentry, scheduler)
  map onto CF's Diego cell/app-instance model — is a sidecar-per-instance pattern already something CF
  could support today, or does it need new primitives?
- Dapr's actor placement service assigns actor instances to specific sidecars — how would that interact
  with CF's own instance placement and rebalancing?
- Is there overlap or conflict between Dapr's workflow durable-execution model and any workflow/orchestration
  primitives CF might introduce for agent task orchestration?
