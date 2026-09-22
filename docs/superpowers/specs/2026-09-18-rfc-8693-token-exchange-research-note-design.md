# RFC 8693 Token Exchange Research Note Design

## Goal

Add a sourced research note on RFC 8693 OAuth 2.0 Token Exchange for delegated agent authority.

## Scope

The note will cover the Security Token Service model, token exchange request/response, subject
and actor tokens, resource/audience/scope targeting, impersonation versus delegation, `act` and
`may_act` claims, and security considerations. It will identify RFC 8693 as an IETF Proposed
Standard and distinguish protocol mechanics from authorization policy and identity issuance.

The Cloud Foundry analysis will map token exchange to UAA, instance identity, service bindings,
agent gateways, least privilege, service-to-service calls, and audit. It will not claim existing
CF/RFC 8693 integration.

## Structure and evidence

Create `research/rfc-8693-token-exchange.md` with the required four sections and frontmatter.
Use RFC 8693 and related OAuth/OIDC references. Clearly distinguish impersonation from delegation
and explain that token exchange does not itself decide whether a requested delegation is allowed.

## Validation

Run Devbox validation and tests, inspect whitespace/staged files, commit the note and plan on
`research/rfc-8693-token-exchange`, push, and open a separate PR targeting `main` without
unrelated artifacts.
