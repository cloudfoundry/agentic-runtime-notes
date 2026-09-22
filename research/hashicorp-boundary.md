---
title: "HashiCorp Boundary for Agent Workload Access"
author: Ruben Koster (@rkoster)
date: 2026-09-22
tags: [authorization, workload-isolation, credentials, security, ecosystem-survey]
cf_areas: [uaa, capi, diego, loggregator]
status: draft
ratings:
  platform-impact:
    value: 78
    note: "Boundary could address access mediation and credential brokering around agent sessions, but would complement rather than replace CF isolation primitives."
  maturity:
    value: 75
    note: "Boundary is an established HashiCorp project with documented operating concepts, while its fit for CF-hosted agent workloads remains unvalidated."
  novelty:
    value: 62
    note: "The access-brokering model is established, but applying it to agent sessions and CF workload identity raises a useful platform-specific connection."
  actionability:
    value: 70
    note: "The model yields concrete questions about identity mapping, target placement, credential ownership, and session lifecycle for a CF prototype."
sources:
  - https://developer.hashicorp.com/boundary/docs/domain-model
  - https://developer.hashicorp.com/boundary/docs/domain-model/workers
  - https://developer.hashicorp.com/boundary/docs/domain-model/targets
  - https://developer.hashicorp.com/boundary/docs/domain-model/sessions
  - https://developer.hashicorp.com/boundary/docs/domain-model/credential-libraries
  - https://developer.hashicorp.com/boundary/docs/concepts/security/permissions
  - https://github.com/hashicorp/boundary
---

## Summary

HashiCorp Boundary is an identity-based access broker for dynamic infrastructure. It authorizes
users to establish sessions to defined targets through workers, and can associate session access
with credentials retrieved from configured credential stores. This makes it relevant to agent
workloads that need narrowly scoped access to tools or infrastructure, but Boundary is an access
plane, not a process, VM, filesystem, or network sandbox; the note is descriptive rather than an
adoption recommendation.

## Key findings

- **Boundary separates authorization from connectivity.** Its domain model organizes identities,
  roles, scopes, projects, targets, hosts, and credential resources. Workers form the data plane:
  they proxy sessions between users and targets and can provide access to private resources without
  exposing their networks directly.
- **Targets are the access unit.** A target represents a networked service with permissions that a
  user can exercise through a session. A role must grant the `authorize-session` permission before
  the user can establish a session to the target. This is a more specific control point than
  giving an agent broad network reachability.
- **Sessions have explicit lifecycle controls.** A session receives an expiration time and
  connection limit from the target. It can be terminated by expiry, cancellation, or removal of a
  resource associated with the session. Boundary documents that credentials associated with the
  session are revoked when the session terminates, while permission changes are evaluated only when
  a session is established.
- **Credential handling can be separated from the agent.** Credential libraries provide credentials
  from a credential store, including integrations that retrieve credentials from Vault. This can
  support per-session or otherwise centrally managed access without placing a long-lived secret in
  an agent image, although the exact lifetime and rotation behavior depends on the credential store
  and integration.
- **Workers are a deployable trust boundary, not an agent sandbox.** Worker placement and tags can
  constrain which workers handle a target, and workers can reach private services. That supports
  network segmentation and brokering, but does not by itself isolate the agent process, its
  filesystem, or its local execution environment.
- **The model is applicable to tool and infrastructure access.** An agent could request access to
  an approved tool endpoint or infrastructure target under a workload identity, with policy
  deciding which target and worker are eligible. The agent would still need separate controls for
  tool semantics, prompt injection, delegated-agent authority, and execution sandboxing.
- **Audit and security are part of the platform model.** Boundary captures data relevant to session
  authorization and retains historical session data in its data warehouse. Operators still need to
  decide which agent context is safe to record and how Boundary events correlate with application,
  request, and tool-invocation records elsewhere.

## CF relevance

Boundary could complement Cloud Foundry rather than replace its workload lifecycle or isolation
mechanisms. CAPI and Diego could continue to schedule and manage the agent application or task, while
Boundary workers mediate narrowly selected connections from that workload to private services,
databases, administrative endpoints, or tool backends. CF identity or workload credentials could be
inputs to a Boundary authentication and authorization flow, but the mapping between a CF user, app,
task, instance, and Boundary principal is not established by these sources.

This division could make the security boundary more explicit: CF governs where the agent runs and
Boundary governs which external targets it may reach and for how long. Worker placement would need
to align with CF networking and foundation or space boundaries, while Loggregator or another audit
pipeline could correlate Boundary session events with app, instance, task, and request identifiers.
Those are integration hypotheses, not existing CF capabilities. In particular, Boundary should not
be presented as the answer to per-session compute isolation; a sandbox or hardened execution
primitive remains necessary for untrusted code and tool processes.

## Open questions

- How should a CF user, application, task, instance, or delegated agent be represented and
  authenticated as a Boundary principal?
- Should Boundary workers run inside CF spaces or foundations, outside them, or in a separate
  security zone, and who operates and updates those workers?
- How can authorization prevent a confused-deputy path when an agent invokes a tool or delegates
  work to another agent?
- Who owns the credential store, and what guarantees do each credential integration and target type
  provide for issuance, rotation, expiration, and revocation?
- How should an app or task exit terminate its Boundary sessions, including sessions opened by
  delegated agents or background tools?
- How should Boundary events correlate with CF app, space, instance, task, user, and request IDs
  without logging sensitive prompts, arguments, or credentials?
- What are the expected latency, availability, retry, and fail-open/fail-closed semantics when the
  Boundary control plane or a worker is unavailable during an agent tool call?
- Which additional primitive should provide process, filesystem, or network sandboxing for code and
  tools that are not trusted merely because their target access was authorized?
