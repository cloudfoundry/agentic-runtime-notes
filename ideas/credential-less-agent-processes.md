---
title: Credential-less agent processes
author: Rashid Rashidov (@rrashidov)
date: 2026-07-08
tags: [identity, sandboxing-isolation]
ratings:
  platform-impact:
    value: 84
    note: 'Initial review of Credential-less agent processes: its subject and tags indicate how broadly the capability could affect an agentic platform.'
  maturity:
    value: 38
    note: 'Initial review of Credential-less agent processes: this score reflects the amount of established external practice visible in the note.'
  novelty:
    value: 80
    note: 'Initial review of Credential-less agent processes: this score reflects how distinct or emerging the approach appears in the current landscape.'
  actionability:
    value: 76
    note: 'Initial review of Credential-less agent processes: this score reflects how readily the material could guide a focused experiment or follow-up.'

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
