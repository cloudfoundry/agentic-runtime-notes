---
title: "SCITT and Agent Action Capsule: Verifiable Agent-Action Provenance"
author: Ruben Koster (@rkoster)
date: 2026-09-17
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
  - https://github.com/ietf-scitt
  - https://datatracker.ietf.org/wg/scitt/about/
  - https://www.rfc-editor.org/rfc/rfc9943
  - https://www.rfc-editor.org/rfc/rfc9942
  - https://github.com/action-state-group/agent-action-capsule
  - https://raw.githubusercontent.com/action-state-group/agent-action-capsule/main/README.md
  - https://datatracker.ietf.org/doc/draft-mih-scitt-agent-action-capsule/
  - https://github.com/action-state-group/agent-action-capsule/blob/main/spec/REGISTRY.md
---

## Summary

SCITT, Supply Chain Integrity, Transparency, and Trust, defines an architecture for registering
statements and obtaining verifiable evidence about their inclusion and history in a
transparency service. Agent Action Capsule is an individual Internet-Draft profile that applies
that model to recording what an AI agent did, including authorization verdicts and refusals.
Together they suggest a way for Cloud Foundry to produce independently verifiable provenance
for agent actions, provided that workload identity, policy context, privacy, and receipt
handling are designed explicitly.

## Key findings

- **SCITT supplies a transparency boundary, not an agent runtime.** The initiative addresses
  end-to-end integrity and trust for statements and artifacts. A transparency service can
  register signed statements and provide receipts that allow later verification of inclusion
  and history without requiring every verifier to trust the original application database.
- **Agent Action Capsule is a statement profile.** It defines a digest-committed JSON record of
  an agent action with signer-independent identity. The profile uses RFC 8785 JSON Canonicalization
  Scheme and a `capsule_id` derived from the capsule content; changing the signature does not
  change the capsule identity.
- **Producer authentication is separate from capsule identity.** One or more independent
  COSE_Sign1 Producer Envelopes can authenticate the raw capsule ID. This allows verifiers to
  reason separately about what was recorded and which producer attested to it.
- **Verdicts include refusals.** The profile records a capsule for every verdict, including a
  blocked or denied action. A refusal therefore becomes affirmative evidence that a policy gate
  evaluated and rejected an action rather than an absence of evidence.
- **Verification has layers.** Capsule Class-1 verification can recompute the content digest
  from capsule bytes without keys, network access, or a clock. Per-envelope cryptographic
  verification and caller-defined signer authorization are separate steps, while optional SCITT
  receipt verification proves transparency-service registration. Merkle data structures belong
  behind the SCITT registration boundary rather than inside capsule construction.
- **The standards status must be stated precisely.** The project README identifies SCITT
  architecture and COSE Receipts as RFC 9943 and RFC 9942. Agent Action Capsule is explicitly
  described as an individual IETF Internet-Draft, not an adopted SCITT Working Group document
  and not an RFC.
- **A capsule can connect authorization to outcome.** A useful action record can include the
  agent subject, requested action, resource, policy decision, inputs or evidence references,
  resulting outcome, and links in a chain of related actions. The exact profile vocabulary and
  registry status remain subject to the draft.
- **CF identity needs an integration boundary.** A proposed CF design would have a gateway or
  policy service verify an instance identity certificate, map the verified workload to a stable
  subject, and include that identity in the capsule. Neither SCITT nor Agent Action Capsule
  should be assumed to validate CF certificates or know CAPI/Diego identity semantics.
- **Platform events can enrich provenance.** CAPI and Diego events could correlate application,
  process, space, binding, deployment, and instance lifecycle with an agent action. Loggregator
  could provide operational correlation, while the capsule/transparency path supplies a durable
  verification record. These systems would need clear ownership to avoid conflicting event IDs
  and incomplete provenance.
- **Privacy is a first-class constraint.** Agent actions may contain prompts, tool arguments,
  credentials, personal data, or sensitive results. A capsule should prefer digests and typed
  references over raw secrets, define redaction and retention policy, and make verifier access
  tenant-aware.

## CF relevance

Cloud Foundry could emit Agent Action Capsules at policy gateways, agent runtimes, tool brokers,
or platform API boundaries. For example, a gateway could verify a CF instance identity
certificate, authenticate the workload as `agent_instance:<id>`, evaluate whether it may invoke
a tool or mutate a resource, and record an allow or refusal capsule containing the subject,
resource, policy reference, and outcome. A transparency service could then provide a receipt for
later audit or independent verification.

This would complement rather than replace Loggregator. Loggregator is useful for operational
streaming, correlation, and alerting; a SCITT-backed record would be designed for durable,
cryptographically verifiable provenance. CAPI and Diego events could supply lifecycle context,
but the system would need to define which component is authoritative for the identity and policy
facts included in a capsule. Service bindings, tool gateways, and agent controllers could all
be capsule producers, but their signatures and authorization scopes must be distinguishable.

The design also changes incident-response and compliance workflows. A denied tool invocation
could be shown as an explicit policy decision, while a successful action could be checked against
the agent identity, authorization state, and transparency receipt. This is valuable only if
certificate rotation, revocation, signer authorization, clock/context claims, privacy, and
retention are handled consistently. CF should avoid recording raw prompts or credentials merely
to obtain auditability.

## Open questions

- What stable subject should a CF capsule use: app, process instance, instance identity
  certificate, agent deployment, or a composite identity?
- Which component verifies instance identity certificates, and how are rotation, revocation,
  process replacement, and delegated authority represented in the capsule chain?
- Which authorization policy inputs and evidence references are necessary to make an allow or
  refusal independently meaningful without storing sensitive request content?
- Should every tool and platform API action produce a capsule, or should policy gateways emit
  capsules only for sensitive, delegated, or cross-tenant operations?
- How should a CF foundation operate or consume a transparency service, and what receipt
  availability and recovery guarantees are required?
- How should signer authorization work when multiple gateways, runtimes, and platform services
  can produce statements for the same agent?
- How should capsule privacy, retention, deletion requests, tenant isolation, and verifier
  access interact with immutable transparency records?
- What is the right relationship between capsule chains, Loggregator correlation IDs, CAPI/Diego
  event IDs, and distributed traces?
