---
title: Agent identity and tool authorization — the platform as the agent's identity provider
author: Wayne E. Seguin (@wayneeseguin)
date: 2026-08-12
tags: [identity, inter-agent-comms, observability-governance]
---

## The idea

Managed agent platforms are converging on the same "identity" pillar, built from three
parts:

1. A **workload identity** for the agent itself.
2. A **credential vault**, so tool secrets never live in the agent's process.
3. **Delegated outbound auth** — the platform mints short-lived, scoped tokens the agent
   uses to call tools on a user's behalf.

AWS ships all three as AgentCore Identity. Google's Agent Engine principals cover the workload-identity part with SPIFFE. Azure's per-deployment Entra identity is inbound-only, and Anthropic ships the vault and a credential proxy with no workload identity at all — the platform that skipped workload identity did so by never letting the agent hold a credential, which is [[credential-less-agent-processes]] in different clothing. The pressure behind all of it is the same: an agent that holds a credential can be talked into leaking it. Identity, delegation, and audit are what the procurement checklists CF's install base folks keep asking for.

**CF operates most of this today.** Diego instance identity certs are a workload identity, carrying `organization:`, `space:`, and `app:` GUIDs as certificate Organizational Units which are the same kind of tenancy tuple Google encodes into SPIFFE IDs and AWS and Azure encode into ARNs and Entra IDs. UAA is a full OAuth authorization server run as core platform infrastructure. CredHub is a secret store rather than a per-user token vault; that vault is the genuinely missing part, and the [[credential-less-agent-processes]] sidecar is its CF-shaped answer. One pair of these components talks today: CredHub accepts an instance identity cert as an mTLS client credential (it requires an `app:<guid>` OU), so the
cert-as-credential pattern this idea turns on is already running inside a core CF component. What's missing is a runtime authorization model connecting the rest: nothing lets a running workload exchange its platform-attested identity for a token, and nothing expresses "agent A may call tool T on behalf of user U" as platform policy.

[RFC-0055](https://github.com/cloudfoundry/community/blob/main/toc/rfc/rfc-0055-identity-aware-routing-for-gorouter.md) (Identity-Aware Routing for GoRouter, Accepted) supplies the *inbound* half of this story which is the default-deny route policies on authenticated caller identity. This idea is the outbound mirror: the same platform-attested identity, carried forward into token issuance and tool authorization.

## Three layers: a precondition, a proposal, and a direction

**Layer 1 :: the precondition: reachability as authorization (RFC-0055 alone).**

Tools and MCP servers hosted on CF get default-deny route policies keyed on the calling app's instance identity cert. "Which agent may reach which tool" becomes platform policy with an audit trail, using only a design already accepted upstream. **No new components.** This is the inbound half, not yet the outbound one, and the granularity is route-level. An agent can reach a tool or it can't, a multi-tool MCP server collapses to all-or-nothing, and nothing covers tools that live off-platform. If RFC-0055 stalls, layers 2 and 3 still stand (they depend on the certs, not the route policies) but this cheap first win disappears.

**Layer 2 :: the proposal: workload token exchange against UAA.**

UAA gains the ability to accept a Diego instance identity cert as a client credential and mint a short-lived workload token carrying the app, space, and org GUIDs as claims. The mechanism is mTLS client authentication per RFC 8705 or token exchange per RFC 8693; UAA implements neither today (it ships `client_secret_basic`, `client_secret_post`, and `private_key_jwt`), though draft POCs of this exchange now exist against UAA (see "Related"). Two things follow:

- **CF-hosted MCP servers get most of an authorization server for free.**
  MCP's authorization framework is OAuth 2.1-based; a CF-hosted MCP server can trust UAA-issued workload tokens with no app-managed secrets on either side, and tool authorization becomes scope policy in an OAuth server the platform already runs, audited through events UAA already emits. The remaining delta (full OAuth 2.1 conformance, RFC 8707 resource indicators, client registration) is real but bounded (see "What to research next"). The bet worth naming: this assumes org-internal MCP servers become a real deployment shape on CF, rather than staying vendor-hosted with only the client on the platform.
- **The [[credential-less-agent-processes]] sidecar gets something standard to hold — for
  tools that trust UAA.**
  For those, the sidecar performs the cert-for-token exchange and injects a short-lived scoped token per request; revocation becomes a UAA action rather than a redeployment (and is real to the extent the tool introspects tokens rather than validating them locally), and a leaked token is bounded twice: scoped to one agent, and expired in minutes. For off-platform SaaS APIs the sidecar still holds the provider key (see "The hard part" below), but the workload token gives it an attested caller identity to
  check before it proxies anything.

**Layer 3 :: the direction: delegation chains as platform policy.**

The platform records *on whose behalf* an agent acts, in the direction the Agent Operation Authorization Token (AOAT) draft points: tokens carry a delegation chain (user → agent → sub-agent → tool), consent is captured as structured evidence, and the platform issues attested, delegation-bearing tokens while the tool enforces policy against them. (AOAT is an individual IETF draft, not yet a working-group document; see `research/open-agent-auth.md`.) That is the delegation half of what AgentCore Identity offers, platform-attested end to end because the workload identity at the bottom of the chain is a cert the operator's own platform minted, though not its third-party token vault, which stays with the sidecar.
This layer is not layer 2 plus extra claims: it needs a user-bound token established at issuance, through a consent step layer 2's two-party exchange never performs. What it shares with layer 2 is the substrate: the same cert, exchanged at the same place.

## The alternative this has to beat

Everything above could be assembled without touching UAA or GoRouter: SPIRE attesting workloads against the Diego instance identity CA, plus any conformant OAuth 2.1 server (Keycloak, Ory Hydra, an existing enterprise IdP) as issuer and consent surface, brokered as a marketplace service. That stack plausibly delivers all three layers with zero platform delta and zero new attack surface on UAA. The platform version buys two things the brokered one can't: every app on the foundation gets it without a tenant opting in, and one identity substrate serves both routing policy (RFC-0055) and token issuance instead of two systems asserting the same facts. Whether those two are worth a UAA change is a question our working group should answer explicitly, not by default.

## Why CF is unusually well-positioned

- **Instance identity certs already carry the right claims.**
  The `organization:`/`space:`/`app:` OUs are the tenancy tuple every platform's agent-identity scheme encodes (the same insight [[dapr-durable-execution-on-cf]] uses for `dapr-sentry`), and the certs behind Google's Agent Engine principals even share Diego's default 24-hour lifetime. No new CA, no second root of trust.
- **CredHub already consumes these certs.** Its mTLS authentication requires an
  `app:<guid>` OU in the client certificate, so UAA would be the second core component to accept them, not the first.
- **UAA is close to the authorization server MCP assumes.**
  MCP standardized on OAuth 2.1 for its HTTP transport; most platforms have to stand up or buy that component. CF has run an authorization server, multi-tenant and at scale, for well over a decade.
- **Service bindings are the declaration surface, not the delivery path.**
  "This app may use this tool" has a natural home in the binding model; the token itself should flow
  through the layer-2 exchange rather than `VCAP_SERVICES`, which the app can read.
- **RFC-0055 supplies the inbound half.**
  Its identity extraction and policy language compose directly with the layer-2 exchange (the identity a route policy admits is the identity a token exchange would attest), and its policy-source syntax reserves `cf:` today while naming `spiffe:` as future extensibility. One identity substrate, both
  directions.
- **The survey says this is the closest gap.**
  Across the managed-platform research notes so far, identity is the pillar where CF's distance to parity is smallest. As opposed to durable execution, where CF is missing the engine entirely, here every load-bearing component except the per-user token vault already exists. What that counting hides is the subject of the next section.

## The hard part

**CF authorizes humans at deploy time; this needs to authorize workloads at runtime.**
Org and space roles answer "who may push and manage apps." Nothing in the platform answers "what may this running process do" which is a class of capability CF has never had. Bolting operation-level policy onto UAA risks turning it into a general-purpose policy engine, a role it was never designed for. The likely shape is UAA staying a token issuer while enforcement lives at the tool — an Open Policy Agent (OPA) or Cedar-style policy engine, as both the AOAT draft and AWS's convergence suggest. The open question is what CF ships so tools don't each write their own enforcement.

Other unresolved pieces:

- **Blast radius of a workload-credential grant.**
  UAA is shared, critical infrastructure, and a new grant type reachable by every app container is new attack surface on the component least tolerant of it. The CA reuse that makes this cheap also concentrates the risk: instance identity certs are signed on every Diego cell, so a compromised cell
  could mint certs and, with this grant, bearer tokens usable from anywhere. Scoping, rate limits, and rotation interplay (instance certs rotate roughly daily by default) need real design, not enthusiasm.
- **Scope semantics.**
  Route-level (layer 1) and operation-level (layer 3) authorization differ by orders of magnitude in policy volume. Per-tool, per-operation scopes across hundreds of MCP servers mean a scope explosion; who curates that namespace?
- **No user at the keyboard.**
  The AOAT flow assumes a human consent step. Autonomous pipelines (schedulers waking agents, agents delegating to agents) need a consent story that doesn't reduce to "pre-approve everything," or the audit trail is theater.
- **Legitimate authority, misused.**
  Short-lived scoped tokens bound leakage; they do nothing about a compromised agent using a valid, correctly-scoped token to do exactly what an injection asked. The platform's contribution is bounding, attributing, and revoking authority — constraining what an agent does *with* that authority is the
  layer 3 policy question, and no token format answers it.
- **Off-platform tools.**
  Layer 2 covers tools that trust UAA. Calls to external SaaS APIs still need the vault-and-proxy pattern from [[credential-less-agent-processes]]; this idea narrows what the sidecar holds but doesn't eliminate the sidecar.

## Why it might matter

Identity and tool authorization is a fourth platform gap our research corpus identifies, alongside durable execution, actor placement, and per-session isolation. And it is the one where CF's answer can be *portable* in a way the hyperscalers' can't: their agent identities only work inside their cloud, while CF's would bottom out in a cert chain the operator controls, wherever CF runs. SPIRE offers the same portability (that is the alternative above), but CF gets it without operating a second identity system. For regulated industries where CF actually lives, "every tool call is traceable to a platform-attested workload identity and a recorded delegation" is the sentence that answers an audit finding.

It also complements the answers to the other three gaps rather than competing with them. Durable agents ([[dapr-durable-execution-on-cf]], [[durable-tasks-for-cf]]) that suspend and resume need an identity that survives the move — the org/space/app tuple does, even though the per-container cert doesn't. Actor-addressed routing ([[dapr-aware-gorouter]]) composes with caller identity per RFC-0055. And per-session sandboxes ([[per-session-sandboxes]]) pose the question layer 3 will eventually face: can app-scoped tokens be subdivided per session, or does that need the per-request virtual-workload
pattern from the IETF's WIMSE (Workload Identity in Multi System Environments) work?

## What to research next

- UAA implements neither RFC 8705 mTLS client authentication nor RFC 8693 token exchange today, but a draft POC of the RFC 8705 half exists: [uaa#3972](https://github.com/cloudfoundry/uaa/pull/3972) exchanges an instance identity cert for a UAA JWT carrying the app, space, and org GUIDs as claims. What is the implementation cost of landing it properly, and how do daily cert rotations interact with token and refresh-token lifetimes?
- Map MCP's authorization requirements onto UAA concretely: full OAuth 2.1 conformance (UAA still ships the implicit and password grants OAuth 2.1 removes), RFC 8707 resource indicators, and Client ID Metadata Documents. How big is the delta for UAA to serve a CF-hosted MCP server out of the box?
- Should workload tokens carry SPIFFE IDs? The namespace RFC-0055 names as future extensibility, and the WIMSE direction the AOAT draft builds on? Can an instance identity cert serve as the workload-identity substrate `research/open-agent-auth.md` asks about for SPIFFE SVIDs? A draft POC probes this direction: [uaa#3968](https://github.com/cloudfoundry/uaa/pull/3968) adds a JWT-SVID signing endpoint to UAA that verifies an instance identity cert and mints a SPIFFE JWT-SVID from its org, space, and app OUs.
- What is the minimum feature set for parity with AgentCore Identity and Agent Engine's principals, and which of their choices (Cedar policies, token vaults, per-session identities) are worth adopting versus avoiding?
- Where should tool-side policy enforcement live on CF, given that UAA should stay a token issuer, e.g. should it be a library tools embed, an OPA sidecar pattern, or route-level enforcement extended with operation awareness?

## Related

- [RFC-0055: Identity-Aware Routing for GoRouter](https://github.com/cloudfoundry/community/blob/main/toc/rfc/rfc-0055-identity-aware-routing-for-gorouter.md) is the inbound half this idea mirrors.
- Sibling ideas: [[credential-less-agent-processes]] (the vault-and-sidecar pattern layer 2 gives a standard token to), [[localhost-only-egress-for-agents]] (the enforcement point for outbound calls), [[per-session-sandboxes]] (the per-session credential question above), and [[dapr-durable-execution-on-cf]] (the same instance-identity-cert insight, applied to Dapr's control plane).
- UAA POC drafts: [uaa#3972](https://github.com/cloudfoundry/uaa/pull/3972) (RFC 8705 mutual-TLS client authentication for instance identity certs, the layer-2 exchange) and [uaa#3968](https://github.com/cloudfoundry/uaa/pull/3968) (a JWT-SVID signing endpoint, the SPIFFE direction from "What to research next").
- Research notes: `research/open-agent-auth.md` (the AOAT delegation and consent model layer 3 follows), `research/mcp-protocol.md` (MCP's OAuth 2.1-based authorization framework), and `research/anthropic-managed-agents.md` (the credential-proxy finding the sidecar pattern descends from).
- Managed-platform notes: `research/aws-agents.md`, `research/vertex-agent-engine.md`, and
  `research/azure-hosted-agents.md` (the identity pillar this idea answers).
