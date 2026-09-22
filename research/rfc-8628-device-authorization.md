---
title: "RFC 8628: Device Authorization for Headless Agents and Remote Workloads"
author: Ruben Koster (@rkoster)
date: 2026-09-18
tags: [identity, authorization, orchestration, ecosystem-survey]
cf_areas: [uaa, capi, diego]
status: draft
ratings:
  platform-impact:
    value: 80
    note: "Device authorization is a practical bridge for connecting headless agents, CLIs, and remote daemons to human identity without embedding a browser."
  maturity:
    value: 88
    note: "RFC 8628 is an IETF Proposed Standard with a defined flow, error behavior, and security considerations."
  novelty:
    value: 52
    note: "The protocol formalizes a constrained-device OAuth pattern rather than introducing an agent-specific delegation model."
  actionability:
    value: 86
    note: "The flow maps directly to CF UAA, remote agent daemons, service bindings, user consent, and token lifecycle operations."
sources:
  - https://www.rfc-editor.org/rfc/rfc8628
  - https://www.rfc-editor.org/info/rfc8628/
  - https://datatracker.ietf.org/doc/rfc8628/
  - https://www.rfc-editor.org/rfc/rfc6749
---

## Summary

RFC 8628 defines the OAuth 2.0 Device Authorization Grant for clients that cannot use a
browser-based authorization flow locally or are difficult to operate interactively. The client
requests a device code and user code, asks the user to authorize on a separate device, and polls
the authorization server until a token is available. This makes it relevant to headless agent
CLIs, remote daemons, coding sandboxes, and CF-hosted workloads, while leaving downstream
delegation and resource policy to other OAuth mechanisms.

## Key findings

- **The flow separates the client from the user agent.** A device client makes outbound HTTPS
  requests and displays a verification URI and code. The user completes authentication and
  consent on a phone or computer, so the client does not need to receive inbound browser traffic.
- **The authorization server returns short-lived flow state.** The device authorization response
  includes a `device_code`, a human-entered `user_code`, a verification URI, an optional complete
  verification URI, an expiration, and a recommended polling interval.
- **The client polls the token endpoint.** Before consent, the token endpoint returns
  `authorization_pending`. The client must respect the interval; `slow_down` increases the
  interval for subsequent requests. After approval, the client receives an OAuth access token
  or another configured token response. Denial and expiry have explicit errors.
- **The user code is usability-sensitive.** Because users type the code, it has lower entropy
  than a bearer token. RFC 8628 requires rate limiting and finite lifetime to make guessing
  infeasible, and recommends user-facing information that helps prevent authorizing an attacker
  controlled device.
- **Device and user codes have different security roles.** The device code is used by the client
  during polling and must be protected as sensitive flow state. The user code is entered by the
  human and needs rate limiting, sufficient entropy, expiration, and phishing defenses.
- **Public clients are supported.** Clients that cannot keep credentials secret identify
  themselves with `client_id`, while confidential clients authenticate according to OAuth rules.
  The grant is therefore suitable for command-line tools, remote daemons, and devices with no
  secure client-secret storage.
- **Polling needs capacity controls.** The protocol explicitly addresses token-endpoint load by
  requiring an interval and warning clients not to begin device authorization automatically on
  every startup or expired session. Implementations need rate limits and retry behavior.
- **Device trust is part of the threat model.** The authorization server cannot assume that a
  device or agent client is trustworthy merely because a user approved a code. Token storage,
  malware, remote phishing, authorization-server choice, and device integrity remain deployment
  concerns.
- **Device authorization is not token exchange.** RFC 8628 obtains user authorization through a
  secondary device. RFC 8693 exchanges an existing subject/actor token for a targeted token.
  A headless agent may use RFC 8628 for initial login and RFC 8693 or another mechanism for
  downstream delegation.
- **RFC 8628 is an IETF Proposed Standard.** It standardizes the flow and security behavior but
  does not define an agent registry, workload identity, consent taxonomy, or resource-specific
  least-privilege policy.

## CF relevance

Cloud Foundry could use RFC 8628 for headless CLIs, remote agent daemons, coding sandboxes, and
automation that cannot open a browser on the execution host. A CLI or daemon could request a
device code from UAA, display the verification URI/code to the user, poll for completion, and
store the resulting token using the daemon's credential and filesystem policy.

The flow also fits remote agents running under Diego or an adjacent sandbox substrate. CAPI
could manage the application or daemon, while a service binding supplies the UAA endpoints and
client identifier. The resulting access token would need bounded scopes and secure persistence;
device authorization alone does not establish that an agent may access every tool or resource
available to the user.

CF operators would need to expose clear device/user consent information, rate-limit polling,
support revocation and logout, and audit the link between device code, user, client/agent,
application instance, and resulting token. For long-running agents, RFC 8628 is primarily an
initial or renewal login mechanism; token exchange, refresh, workload identity, or a delegation
broker may be needed to obtain resource-specific and renewable authority.

## Open questions

- Should CF UAA expose RFC 8628 for remote agent daemons and headless platform clients?
- How should a device authorization request identify the CF application, agent, sandbox, or
  daemon without confusing the runtime identity with the consenting user?
- Where should tokens be stored for Diego processes, remote daemons, and disposable sandboxes,
  and how should replacement or migration affect them?
- How should device flow scopes combine with RFC 8693 exchange, agent delegation, and service
  binding policy?
- What polling, expiry, retry, and revocation behavior should CF enforce across many agents?
- How should user consent, device details, client identity, token issuance, and downstream agent
  actions be correlated in Loggregator and protected audit records?
- Which phishing, device-trust, and user-code protections should be added beyond the RFC when
  the client is an autonomous or semi-autonomous agent?
