---
title: Credential-less agent processes
author: Rashid Rashidov (@rrashidov)
date: 2026-07-08
tags: [identity, sandboxing-isolation]
ratings:
  platform-impact:
    value: 50
    note: 'CF can bind and store service credentials, but it exposes them to the app process; a platform-held credential and localhost request proxy are missing.'
  maturity:
    value: 75
    note: 'Credential vaults and outbound credential proxies are production-capable patterns used by managed agent platforms, though the note leaves CF provisioning and multi-tenant bindings unresolved.'
  novelty:
    value: 25
    note: 'Keeping secrets in a local proxy is an established vault-and-sidecar architecture, here applied to prompt-injection risk in agent processes.'
  actionability:
    value: 50
    note: 'The standard-provider API over localhost supplies a plausible prototype boundary, but credential storage, sidecar provisioning, rotation, and per-user tenancy need design first.'

---

## The idea

Credentials handed to an agent process — API keys, OAuth tokens, bound service
credentials — are one prompt injection away from exposure. The process that can call the
model is also the process that can be told to print its environment.

CF should let a developer **bind a provider without the credential ever entering the
process**. The developer declares the binding in the manifest (e.g. `bindings: [anthropic]`);
at runtime the app calls a `localhost` sidecar that proxies the request to the real
provider using a credential it holds but the app cannot read. From the app's perspective
it speaks the standard provider API; it just never sees the key. Revoking or rotating
the credential is an operator action, not a redeployment.

How the credential is stored, how the sidecar is provisioned, and how per-user
multi-tenant bindings work is open for the platform experts to propose.

## Related

- The `localhost` sidecar is a natural fit for the egress proxy in
  [[localhost-only-egress-for-agents]].
- The process boundary assumed here is strengthened by
  [[stronger-workload-isolation-for-agents]].
