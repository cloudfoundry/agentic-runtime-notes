---
title: Stronger workload isolation for agent workloads
author: Rashid Rashidov (@rrashidov)
date: 2026-07-08
tags: [sandboxing-isolation, runtime-lifecycle]
ratings:
  platform-impact:
    value: 50
    note: 'CF supplies container isolation but offers no gVisor- or Kata-style runtime choice to put inference-selected code behind a user-space or dedicated-kernel boundary.'
  maturity:
    value: 75
    note: 'The 75 reflects production-capable gVisor, Kata, and Kubernetes RuntimeClass isolation technologies; it does not imply maturity for manifest-selectable isolation through Garden and Diego, which has no demonstrated implementation, lifecycle integration, or CF operational evidence.'
  novelty:
    value: 25
    note: 'A manifest-selectable sandbox runtime is the familiar RuntimeClass pattern adapted to CF applications that execute unreviewed agent-generated instructions.'
  actionability:
    value: 50
    note: 'The runtime: sandbox field and gVisor target define a plausible spike, but the Garden or Diego enforcement point, lifecycle wiring, and operator policy are still open.'

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
