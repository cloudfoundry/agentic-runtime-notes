---
title: "Agentic Identity Broker: Delegated OAuth and Credential Mediation"
author: Ruben Koster (@rkoster)
date: 2026-09-18
tags: [authorization, identity, observability-governance, ecosystem-survey]
cf_areas: [uaa, capi, diego, loggregator]
status: draft
ratings:
  platform-impact:
    value: 86
    note: "Delegated, revocable agent access to third-party services is a central platform problem as agents act with user authority."
  maturity:
    value: 62
    note: "The broker has a clear documented model and API architecture, but its adoption and production integration with CF remain to be evaluated."
  novelty:
    value: 78
    note: "The combination of human-readable permission sets, encrypted token custody, and request-time RFC 8693 exchange addresses a specific agent credential gap."
  actionability:
    value: 84
    note: "The principal/agent/grant model maps directly to UAA, CF workload identity, service bindings, and gateway policy decisions."
sources:
  - https://agenticidentitybroker.dev/
  - https://agenticidentitybroker.dev/docs/concepts
  - https://agenticidentitybroker.dev/docs/concepts/architecture
  - https://agenticidentitybroker.dev/docs/concepts/delegation-and-consent
  - https://agenticidentitybroker.dev/docs/concepts/token-exchange
  - https://agenticidentitybroker.dev/docs/concepts/encryption
  - https://agenticidentitybroker.dev/api/enduser
---

## Summary

Agentic Identity Broker is identity infrastructure for agents that act on a user's behalf. It
models per-user, per-agent, per-service delegation with scoped permission sets, expiry, and
revocation, while keeping third-party access and refresh tokens in an encrypted broker vault.
At request time, a trusted gateway exchanges an agent token for the appropriate provider token
using RFC 8693. For Cloud Foundry, it provides a concrete pattern for separating workload
identity, human consent, authorization, and third-party credential custody.

## Key findings

- **Delegation is explicit and scoped.** A principal grants an agent permission sets for named
  third-party services. A user has at most one active grant for each agent, a grant may expire,
  and a user can revoke selected permissions or the complete grant.
- **The broker defines useful policy objects.** Agents have canonical IDs and declare required
  services and permission sets. Services represent OAuth providers and protected resources.
  Permission sets translate provider scopes into human-readable business permissions that users
  can understand during consent.
- **Authentication and authorization are separate.** The broker does not authenticate users.
  A trusted reverse proxy authenticates each request and passes the principal identifier to the
  broker. The broker then evaluates consent, grants, expiry, and service access.
- **The deployment has separate trust surfaces.** A single Go broker exposes an end-user port
  for APIs, consent UI, and OAuth endpoints, and an internal admin port for administrators and
  automation. Operators can expose and secure these surfaces independently.
- **Agents do not receive provider credentials.** The broker stores third-party access and
  refresh tokens in encrypted user sessions. Agents hold broker-issued or upstream agent tokens,
  not long-lived provider tokens that would be difficult to revoke or attribute.
- **Token exchange happens at request time.** An agent gateway presents an agent token, target
  resource, and a signed client assertion. The broker validates the gateway, derives user and
  agent identity from the subject token, checks the active grant, selects the configured service,
  refreshes the stored credential if needed, and returns the provider token.
- **Exchange creates an audit boundary.** The exchange identifies the user, agent, gateway, and
  protected resource. This enables attribution without requiring the agent itself to hold the
  provider credential or expose it in tool/runtime logs.
- **An optional Envoy ExtProc integrates at the edge.** The broker documents a standalone gRPC
  External Processor sidecar that exchanges agent tokens for provider tokens on requests through
  an Envoy-based agent gateway. It can cache results in memory and use OPA policy to restrict
  proxied requests.
- **Encryption is mandatory.** Third-party access tokens, refresh tokens, and service client
  secrets are encrypted before storage, with ciphertext bound to the service. Production uses
  envelope encryption with AWS KMS and cached branch keys; development has a raw-key backend.
  The broker does not provide a plaintext fallback.
- **Agent identity can be metadata-backed.** The broker can associate an agent with a Client ID
  Metadata Document URL and validate the resulting metadata for the consent interface. This is
  useful for governance, but the deployment still needs a trusted way to identify the calling
  agent and gateway.

## CF relevance

Cloud Foundry could use this model to keep UAA or platform workload authentication separate from
delegated access to GitHub, Google, Databricks, internal APIs, or other services. A CF-hosted
agent would receive a scoped broker token through a binding or workload identity flow. A gateway
would exchange that token only when the agent invokes an approved resource, while the provider
credential remains in the broker's vault.

The mapping has several possible boundaries. UAA could authenticate users and issue or validate
agent-facing identities; CF instance identity certificates could identify the running workload;
and a service broker could provision a delegation broker or service-specific permission sets.
An Envoy or CF routing gateway could perform the request-time exchange, while CAPI/Diego
lifecycle events could inform revocation when an app, instance, space, or binding disappears.

The important platform property is least privilege with attribution. Service bindings should
not distribute broad third-party refresh tokens to every agent instance. Instead, a binding or
gateway policy should identify the agent and target resource, and the broker should enforce the
active user grant. Loggregator or a protected audit store could correlate user, agent, gateway,
resource, grant, exchange, and resulting operation without recording provider secrets.

## Open questions

- What is the canonical agent identity in CF: app, process instance, instance certificate,
  service account, agent registration, or a composite identity?
- Should UAA, a CF gateway, or the broker own token issuance and validation for agent-facing
  credentials?
- How should delegated authority interact with instance identity when an application scales,
  restages, or moves between Diego cells?
- Which component performs RFC 8693 exchange, and how should target resource, provider, and
  service-binding policy be configured and audited?
- How quickly must grant revocation, certificate revocation, app deletion, and binding removal
  stop future exchanges?
- How should permission sets map to CF orgs, spaces, apps, tools, service instances, and
  external provider scopes?
- Which exchange metadata belongs in Loggregator, and which sensitive consent or token data must
  remain in a restricted audit store?
- How should the broker's encrypted token vault, KMS dependency, key rotation, backup, and
  recovery be operated by a CF foundation?
