---
title: Stronger workload isolation for agent workloads
author: Rashid Rashidov (@rrashidov)
date: 2026-07-08
tags: [sandboxing-isolation, runtime-lifecycle]
ratings:
  platform-impact:
    value: 84
    note: 'Initial review of Stronger workload isolation for agent workloads: its subject and tags indicate how broadly the capability could affect an agentic platform.'
  maturity:
    value: 38
    note: 'Initial review of Stronger workload isolation for agent workloads: this score reflects the amount of established external practice visible in the note.'
  novelty:
    value: 80
    note: 'Initial review of Stronger workload isolation for agent workloads: this score reflects how distinct or emerging the approach appears in the current landscape.'
  actionability:
    value: 76
    note: 'Initial review of Stronger workload isolation for agent workloads: this score reflects how readily the material could guide a focused experiment or follow-up.'

---

## The idea

Agent workloads run instructions chosen at inference time — the code that executes is not
something a developer reviewed. A shared kernel with other tenants is a meaningful attack
surface that traditional app workloads don't expose in the same way.

CF should offer a **gVisor-backed runtime option** for apps that need stronger isolation.
From the developer's side this would look like a manifest field — something like
`runtime: sandbox` — that opts the app into a user-space kernel boundary without any other
change to how the app is pushed, scaled, or observed. Operator policy could make it the
default for orgs that host agent workloads.

The design of the enforcement point, and how gVisor (or an equivalent) is wired into the
container lifecycle, is open for the platform experts to propose.

## Related

- `research/k8s-agent-sandbox.md` — documents how k8s-sigs uses `runtimeClassName` to
  decouple the isolation mechanism (gVisor, Kata) from the workload API; the pattern is
  directly relevant here.
- Companion ideas that build on this foundation:
  [[localhost-only-egress-for-agents]], [[credential-less-agent-processes]].
