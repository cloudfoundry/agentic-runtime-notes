---
title: "RFC 8693: OAuth 2.0 Token Exchange for Delegated Agent Authority"
author: Ruben Koster (@rkoster)
date: 2026-09-18
tags: [authorization, identity, inter-agent-comms, ecosystem-survey]
cf_areas: [uaa, capi, diego]
status: draft
ratings:
  platform-impact:
    value: 88
    note: "Token exchange provides a standardized mechanism for agents and services to obtain narrowly targeted credentials without sharing broad user tokens."
  maturity:
    value: 86
    note: "RFC 8693 is an IETF Proposed Standard with established OAuth and Security Token Service terminology."
  novelty:
    value: 58
    note: "The protocol formalizes established STS impersonation and delegation patterns rather than defining an agent-specific identity model."
  actionability:
    value: 90
    note: "The subject/actor/audience model maps directly to CF UAA, workload identity, service bindings, and agent gateway authorization."
sources:
  - https://www.rfc-editor.org/rfc/rfc8693
  - https://www.rfc-editor.org/info/rfc8693/
  - https://datatracker.ietf.org/doc/rfc8693/
  - https://www.rfc-editor.org/rfc/rfc6749
---

## Summary

RFC 8693 defines an HTTP and JSON protocol for OAuth 2.0 token exchange through a Security Token
Service. A client presents a subject token, optionally an actor token, and target parameters to
obtain a new token appropriate for a resource or audience. The protocol supports impersonation
and delegation, making it a foundational mechanism for agents that need scoped authority without
holding broad user or provider credentials.

## Key findings

- **RFC 8693 standardizes an STS interaction.** It defines how a client requests a security
  token from an OAuth authorization server using the token-exchange grant type. The server
  validates the presented token(s), applies policy, and issues a token for the requested use.
- **The request carries explicit context.** Exchange parameters include `subject_token`, its
  type, optional `actor_token`, target `resource`, logical `audience`, requested `scope`, and
  requested token type. These fields let a deployment bind the issued token to a target service
  and constrained authority.
- **Impersonation and delegation differ.** In impersonation, the client acts as the subject and
  the issued token can preserve the subject identity without identifying a distinct actor. In
  delegation, the subject is the party on whose behalf action occurs and the actor token
  identifies the party currently acting.
- **The `act` claim preserves actor context.** RFC 8693 examples show an issued token with
  `sub` identifying the subject and `act.sub` identifying the delegated actor. This preserves
  accountability while allowing the actor to use a token targeted at a downstream service.
- **`may_act` can constrain delegation.** A subject token can express an actor authorized to act
  on its behalf. The authorization server still decides whether the requested exchange is
  allowed, how scopes are reduced, and what claims appear in the issued token.
- **Targeting is a security boundary.** `resource` identifies a protected resource URI and
  `audience` identifies a logical target service. The target service can reject a token issued for
  another audience, reducing the value of a token leaked outside its intended path.
- **Token exchange is not authorization policy by itself.** RFC 8693 defines protocol fields and
  flows, but deployments choose trusted issuers, token validation, allowed actors, scope
  reduction, audience/resource policy, token lifetime, revocation, and key management.
- **The issued token is a new credential.** Exchange does not merely forward the subject token;
  it produces a token with the authorization server's issuer, target, lifetime, scopes, and
  identity/delegation context. Downstream services must validate the new token and enforce their
  own resource policy.
- **The model supports multi-hop services.** A service can exchange or pass delegated authority
  onward when policy permits, but each hop increases the need for bounded scopes, actor-chain
  visibility, audience restrictions, and reliable audit.
- **RFC 8693 is an IETF Proposed Standard.** It is a protocol foundation, not a complete agent
  identity system, consent UX, credential vault, or workload lifecycle mechanism.

## CF relevance

Cloud Foundry could use RFC 8693 to let an agent exchange a user or workload token for a
resource-specific token without receiving a broad credential. UAA could participate as the
authorization server or trusted issuer, while a CF instance identity certificate identifies
the running workload. A gateway could exchange the agent's subject/actor context for a token
targeted at a service, tool, route, or downstream application.

Service bindings could carry exchange endpoints and constrained client credentials rather than
long-lived provider secrets. The resulting token could identify the user in `sub`, the agent or
gateway in `act`, and the target CF service in `aud` or `resource`. CAPI and Diego lifecycle
events could inform revocation when an application, process instance, binding, or delegation is
removed, while Loggregator could correlate exchange, downstream request, policy decision, and
outcome.

The protocol does not remove the need for CF policy. A platform must decide which workloads may
act for which users, how scopes are narrowed, whether nested delegation is allowed, how short
tokens live, and how token exchange is audited. RFC 8693 is therefore a useful interoperability
boundary for an identity broker or gateway, not a substitute for UAA governance or application
authorization.

## Open questions

- What should `sub` and `act` represent for CF users, app instances, agents, gateways, and
  delegated tools?
- Should UAA issue exchange tokens directly, or should a dedicated agent identity broker sit
  between UAA and downstream services?
- How should `resource` and `audience` map to CF apps, routes, service instances, tools, and
  external providers?
- Which scopes may be exchanged, and how must every delegation hop reduce or preserve authority?
- How should instance replacement, certificate rotation, grant revocation, and user logout
  invalidate exchanged tokens?
- What token lifetime and replay protections are appropriate for long-running agent tasks?
- How should nested `act` chains and exchange events appear in Loggregator, audit records, and
  downstream authorization decisions?
