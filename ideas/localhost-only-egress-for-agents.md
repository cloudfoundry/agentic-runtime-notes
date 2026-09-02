---
title: Localhost-only egress for agent workloads
author: Rashid Rashidov (@rrashidov)
date: 2026-07-08
tags: [sandboxing-isolation, observability-governance]
ratings:
  platform-impact:
    value: 75
    note: 'CF lacks a platform-owned, non-bypassable outbound proxy that turns declared external bindings into enforced destinations and request-level audit logs for agent traffic.'
  maturity:
    value: 75
    note: 'The 75 reflects mature, widely deployed proxy, allowlist, interception, and request-logging technologies; it does not imply maturity for the proposed non-bypassable CF integration, binding-derived policy, or ownership model, which lack implementation evidence.'
  novelty:
    value: 25
    note: 'The architecture applies conventional mandatory-egress-proxy and allowlist controls to inference-selected destinations rather than creating a new networking mechanism.'
  actionability:
    value: 50
    note: 'Declared bindings, a localhost endpoint, enforced forwarding, and logging give a prototype outline, but the proxy component, bypass prevention, and policy ownership remain unspecified.'

---

## The idea

An agent's outbound calls are decided at inference time — the developer cannot enumerate
them statically, and a misconfigured or prompt-injected agent can silently reach unintended
hosts. Direct network access from the agent process makes this uninspectable by default.

CF should route all outbound agent traffic through a **platform-owned proxy** that the
workload cannot bypass. From the developer's side, the app manifest would declare the
external bindings it needs (e.g. a model provider, a tool endpoint); the platform provides
a `localhost` address the app calls, and the proxy handles the real outbound connection,
enforcing the declared policy and logging every request. The app code doesn't change — only
the target hostname does.

What the proxy component looks like and who owns the egress policy (developer, operator,
or both) is open for the platform experts to propose.

## Related

- Assumes the isolation foundation in [[stronger-workload-isolation-for-agents]] — a
  network boundary is only as strong as the process boundary underneath it.
- Sibling idea about credentials the proxy can protect: [[credential-less-agent-processes]].
