---
title: "Open Agent Auth — IETF Agent Operation Authorization"
author: Ruben Koster (@rkoster)
date: 2026-07-02
tags: [identity]
cf_areas: [uaa]
status: draft
sources:
  - https://github.com/alibaba/open-agent-auth
  - https://datatracker.ietf.org/doc/draft-liu-agent-operation-authorization/
---

## Summary

Open Agent Auth is an enterprise-grade authorization framework from Alibaba implementing
the IETF Agent Operation Authorization Token (AOAT) protocol (draft-02, March 2026). It
provides cryptographic identity binding between the human user, the agent workload, and the
operation being authorized — covering fine-grained operation authorization, request-level
isolation, and a semantic audit trail. It builds on OIDC, OAuth 2.0 PAR, and the IETF
WIMSE (Workloads In Multi-Service Environments) specification.

## Key findings

- **Three-layer cryptographic identity binding**: (1) User Identity Layer — OIDC ID Token
  with `sub` claim for the authenticated user; (2) Workload Identity Layer — Workload
  Identity Token (WIT) bound to the user via `agent_identity.issuedTo`; (3) Authorization
  Layer — AOAT carrying the workload identity. The three-way invariant is enforced:
  `ID Token.sub == WIT.agent_identity.issuedTo == AOAT.sub`.
- **WIMSE virtual workload pattern**: Each user request gets a dedicated virtual workload
  with a temporary ECDSA P-256 key pair. Isolation is at request level, not
  process/container level. The WIT and WPT (Workload Proof Token) provide cryptographic
  proof of the binding. Virtual workloads expire automatically (default 1 hour).
- **Authorization flow**: User authenticates → agent creates virtual workload and obtains a
  WIT → agent submits a Pushed Authorization Request (PAR) containing the ID Token and WIT
  → Authorization Server validates the binding and presents a consent UI → user approves →
  AS issues an AOAT → agent presents the AOAT to the Resource Server, which enforces an OPA
  policy and executes or denies.
- **AOAT JWT claims**: The token carries `agent_identity` (verified agent-user binding),
  `agent_operation_authorization` (policy reference), `evidence` (user confirmation record,
  AS-signed or W3C VC), `context` (structured input for OPA), and `delegation_chain` (for
  multi-agent delegation).
- **Agent-to-agent delegation**: The `delegation_chain` claim carries an ordered list of
  delegation events, enabling multi-agent systems to propagate and audit delegated authority
  across hops.
- **Semantic audit trail**: Each AOAT encodes what the user consented to in structured,
  machine-readable form — not just who acted, but what was authorized and on what evidence.

## CF relevance

SPIFFE/SVID-based workload identity (the direction of several CF RFCs) answers "who is
this agent?" Open Agent Auth answers a different question: "what is this agent authorized
to do, and on whose behalf?" The two are complementary — SPIFFE provides the identity
substrate that WIMSE WITs could be built on, while AOAT adds the operation authorization
layer on top. The IETF draft standardizing AOAT is worth tracking as a potential building
block for CF's agent authorization story, particularly for enterprise use cases where
user consent, per-operation authorization, and immutable audit trails are requirements.

## Open questions

- How does SPIFFE workload identity map to WIMSE WIT in practice — can SPIFFE SVIDs serve
  as the workload identity substrate for AOAT issuance?
- The authorization flow assumes a human-in-the-loop consent step; how does this work for
  fully autonomous agent pipelines with no user present at authorization time?
- Is the IETF AOAT draft on a standards track, or still exploratory? What is the likelihood
  of broad adoption outside the Alibaba ecosystem?
- How does the `delegation_chain` interact with A2A protocol's agent-to-agent calls — do
  they address the same delegation problem at different layers?
