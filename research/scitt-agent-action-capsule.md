---
title: "SCITT and Agent Action Capsule: Verifiable Agent-Action Provenance"
author: Ruben Koster (@rkoster)
date: 2026-11-03
tags: [observability-governance, authorization, identity, ecosystem-survey]
cf_areas: [uaa, capi, diego, loggregator]
status: draft
ratings:
  platform-impact:
    value: 83
    note: "Verifiable action records could support governance, incident response, and compliance for agents operating across CF tenants and services."
  maturity:
    value: 57
    note: "SCITT architecture and receipt work is standardized, while Agent Action Capsule remains an individual Internet-Draft profile under active development."
  novelty:
    value: 79
    note: "The capsule profile treats refusals and authorization verdicts as durable evidence and separates content identity from producer signatures."
  actionability:
    value: 73
    note: "CF can prototype provenance at gateways and policy decisions, but identity mapping, privacy, retention, and transparency-service operations remain design work."
sources:
  - https://datatracker.ietf.org/doc/draft-mih-scitt-agent-action-capsule/
  - https://www.ietf.org/archive/id/draft-mih-scitt-agent-action-capsule-05.html
  - https://www.rfc-editor.org/rfc/rfc9943
  - https://www.rfc-editor.org/rfc/rfc9942
---

## Summary

Agent Action Capsule is a proposed SCITT statement profile for recording what an AI agent
actually did, including refusals, errors, timeouts, and the evidence supporting a reported
effect. This note examines revision `-05`, published 26 September 2026: an individual
Internet-Draft and work in progress, not an adopted SCITT Working Group document or an RFC.
Its separation of content identity, producer authentication, and optional transparency receipts
could help Cloud Foundry produce independently verifiable action records, with explicit limits
on what those records establish about runtime honesty and external outcomes.

## Key findings

- **The profile records “did,” rather than granting “may.”** Authorization records precede
  execution; capsules capture the resulting disposition and evaluated deterministic constraints.
  A conforming producer records every verdict, including blocked, denied, errored, and timed-out
  actions. Refusals become positive evidence of a gate firing rather than disappearing from a
  success-only audit trail ([§1][draft-intro], [§5.5.3][draft-every-verdict]).
- **Content identity survives signing-key rotation.** The `capsule_id` is SHA-256 over RFC 8785
  JSON Canonicalization Scheme bytes, excluding the ID itself. Separate COSE_Sign1 Producer
  Envelopes authenticate the raw capsule ID, so a new signature need not change the record's
  identity. An authenticated key still needs an external authorization rule; signature validity
  alone does not establish authority to speak for a workload ([§3][draft-identity],
  [§5.1][draft-parties],
  [§13][draft-security]).
- **Dispatch and confirmation are distinct.** A confirmed effect requires a well-formed
  `response_digest`. Verdict reason and effect mode are independent: a timeout before dispatch
  has `not_applicable` effect mode, while one after dispatch has `dispatched_unconfirmed`.
  This preserves uncertainty about side effects instead of treating every timeout as a safe
  failure ([§5.3][draft-effect], [§5.5.2][draft-verdict]).
- **Human handoff is not human approval or execution.** A `hitl_dispatched` verdict is
  non-executing; an executing closure is an `executed` capsule linked with `supersedes` to the
  deferral. A non-executing closure uses `resolved`. These distinctions keep a review request
  from being mistaken for a completed action ([§5.5.2–§5.5.4][draft-verdict]).
- **Payload verification has two classes.** Class 1 checks structure, digest identity,
  registry vocabularies, effect/attestation validity, chain semantics, and assurance claims
  without a constraint manifest. Class 2 additionally checks evidence schemas and thresholds
  against the producer's manifest and private evidence. Producer Envelope and receipt results
  remain independent of payload Class 1 ([§6–§8.2][draft-verification]).
- **Transparency is a separate, optional layer.** SCITT architecture ([RFC 9943][scitt]) and
  COSE Receipts ([RFC 9942][receipts]) are Proposed Standards. The capsule profile separately
  registers its ID through a SCITT registration statement; the Producer Envelope is not that
  registration statement. Receipts provide evidence of registration, while capsule verification
  supplies the agent-specific checks ([§3.3][draft-registration]).
- **Tamper evidence is not runtime honesty.** A `confirmed` effect proves that the producer
  bound an observed response, not that the external world reached the claimed state. Spoofed
  upstream responses and dishonest producers remain trust concerns. Likewise, a receipt for a
  submitted record cannot establish that every real-world action was recorded
  ([§13][draft-security]).
- **Privacy rules are stricter than “hash sensitive fields.”** The draft separates clear-safe
  opaque correlation handles, digest-only payload content retained under deployment controls,
  and data that never enters a capsule. End-user identifiers and credentials must be excluded
  both in clear and as digests; low-entropy identifiers are recoverable by dictionary attack.
  Pairwise or encrypted correlation identifiers are recommended where subject correlation is
  genuinely required ([§14.1][draft-privacy]).
- **Vocabulary remains provisional.** The draft proposes registries, but names the source
  repository's `REGISTRY.md` as the interim registry of record until RFC publication. A prototype
  should pin the draft and registry version rather than assume stable IANA assignments
  ([§12.1][draft-iana]).

## CF relevance

A possible CF integration is a tool gateway that authenticates a workload using its instance
identity certificate, evaluates policy, and records the disposition together with effect evidence.
A denied request would produce a refusal capsule; a dispatched request that times out would remain
unconfirmed; an observed response could be bound by digest. This is an integration hypothesis:
the draft defines neither CF certificate validation nor CAPI/Diego identity mapping.

The gateway would need its own producer-key authorization policy and a privacy-reviewed mapping
from workload context to capsule fields. UAA user IDs, bearer tokens, and session identifiers
should not be copied or hashed into capsules. CAPI/Diego lifecycle events and Loggregator traces
could be joined through admitted opaque handles, with sensitive content and identity mappings
kept in separately controlled stores. Operational logs would remain useful alongside durable,
verifiable action records.

A bounded prototype could exercise denial, confirmed response, post-dispatch timeout, and human
handoff, checking that a verifier distinguishes payload validity, producer authenticity, signer
authority, and transparency receipt status. Useful measurements would include capture overhead,
crash/retry gaps, and receipt backlog recovery. This could inform governance and incident response
without implying that capsules provide authorization enforcement, sandboxing, or proof of an
external business outcome.

## Open questions

- Which component can reliably observe both policy decisions and tool effects, including refusals
  and crashes, and how would CF detect actions bypassing that capture boundary?
- How should app, task, process, and instance identities map to producer authority and opaque
  correlation handles without admitting end-user identity or credentials?
- How are certificate/key rotation, revocation, delegated authority, and configuration epochs
  related across producers and verifiers?
- Who retains constraint manifests and detached evidence, and which tenant-aware access controls
  let a later auditor perform Class 2 verification after an application has disappeared?
- How should retries and human handoffs form capsule chains without implying exactly-once effects
  or equating an observed response with independently confirmed external state?
- Should a foundation operate a transparency service or consume one, and what happens to action
  processing when registration is unavailable or receipt delivery is delayed?
- How do retention/deletion requirements for detached evidence and identity mappings interact with
  immutable digest commitments and the ability to verify historical records?

[draft-intro]: https://www.ietf.org/archive/id/draft-mih-scitt-agent-action-capsule-05.html#section-1
[draft-identity]: https://www.ietf.org/archive/id/draft-mih-scitt-agent-action-capsule-05.html#section-3
[draft-registration]: https://www.ietf.org/archive/id/draft-mih-scitt-agent-action-capsule-05.html#section-3.3
[draft-parties]: https://www.ietf.org/archive/id/draft-mih-scitt-agent-action-capsule-05.html#section-5.1
[draft-effect]: https://www.ietf.org/archive/id/draft-mih-scitt-agent-action-capsule-05.html#section-5.3
[draft-verdict]: https://www.ietf.org/archive/id/draft-mih-scitt-agent-action-capsule-05.html#section-5.5.2
[draft-every-verdict]: https://www.ietf.org/archive/id/draft-mih-scitt-agent-action-capsule-05.html#section-5.5.3
[draft-verification]: https://www.ietf.org/archive/id/draft-mih-scitt-agent-action-capsule-05.html#section-6
[draft-iana]: https://www.ietf.org/archive/id/draft-mih-scitt-agent-action-capsule-05.html#section-12.1
[draft-security]: https://www.ietf.org/archive/id/draft-mih-scitt-agent-action-capsule-05.html#section-13
[draft-privacy]: https://www.ietf.org/archive/id/draft-mih-scitt-agent-action-capsule-05.html#section-14.1
[scitt]: https://www.rfc-editor.org/rfc/rfc9943
[receipts]: https://www.rfc-editor.org/rfc/rfc9942
