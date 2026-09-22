# RFC 8628 Device Authorization Research Note Design

## Goal

Add a sourced research note on RFC 8628 OAuth 2.0 Device Authorization Grant for headless
agents, CLIs, remote daemons, and constrained devices.

## Scope

The note will cover the device authorization request/response, device and user codes,
verification URI, user approval on a secondary device, polling, token issuance, discovery, and
security considerations including brute force, phishing, device trust, and polling control.
It will identify RFC 8628 as an IETF Proposed Standard.

The Cloud Foundry analysis will map device authorization to UAA, remote agent daemons, service
bindings, human consent, headless workloads, token storage, polling, revocation, and audit. It
will not claim existing CF/RFC 8628 integration.

## Structure and evidence

Create `research/rfc-8628-device-authorization.md` with the required four sections and
frontmatter. Use RFC 8628, RFC Editor metadata, and OAuth references. Clearly distinguish device
authorization from agent delegation and token exchange: device flow obtains initial user consent;
it does not itself define downstream resource delegation policy.

## Validation

Run Devbox validation and tests, inspect whitespace/staged files, commit the note and plan on
`research/rfc-8628-device-authorization`, push, and open a PR targeting `main` without unrelated
artifacts.
