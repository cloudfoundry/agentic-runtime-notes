---
title: Dapr durable execution on CF, built on CF's own identity and config primitives
author: Ruben Koster (@rkoster)
date: 2026-08-11
tags: [runtime-lifecycle, orchestration, identity, inter-agent-comms]
---

## The idea

Cloud Foundry has no durable-execution primitive. There is no way for a CF app to say "run
this multi-step process, survive a crash or a restart mid-way, and resume exactly where it
left off" — no workflow engine, no virtual actors, no durable timers or reminders. `cf
run-task` is one-shot and fire-and-forget. Agentic workloads make this gap acute: an agent's
reasoning loop is a long-running, tool-calling, human-interruptible process that today has
nowhere durable to live on CF.

Dapr has exactly these primitives — Workflow (durable execution), Actors (the virtual-actor
runtime underneath it), and Jobs/Reminders (durable scheduling) — behind a language-agnostic
HTTP/gRPC API served by a sidecar. The interesting question is therefore not "should CF adopt
Dapr" but **which parts of Dapr's control plane CF already has an equivalent for, and which
are genuine gaps worth adopting upstream.**

The observation that makes this tractable: **CF already owns the hardest part of Dapr's
control plane — workload identity.** A Diego instance identity certificate already carries

```
OU=app:<app-guid>, OU=space:<space-guid>, OU=organization:<org-guid>
```

which is precisely the `(app-id, namespace)` tuple that `dapr-sentry` exists to mint SPIFFE
identities for. A **Dapr namespace maps cleanly onto a CF org/space combination**, and since
Dapr v1.14 actor placement tables are namespace-scoped, with namespace claims verified against
the caller's SPIFFE identity whenever mTLS is enabled. CF's instance identity certs make that
verification trustworthy by construction, rather than by operator diligence.

## Control plane: what CF already has vs. what it would need

| Dapr control-plane component | Does CF have an equivalent? | Sketch |
|---|---|---|
| **`dapr-sentry`** — CA issuing SPIFFE workload identities | **Yes** — the Diego instance identity CA, whose certs already encode app/space/org GUIDs | Bridge rather than run a second CA. Derive the Dapr workload identity from the cert CF already issues; no new root of trust, no new secret to rotate, no second CA to blast-radius. |
| **`dapr-operator`** — watches Component CRDs, pushes component config to sidecars | **Yes** — CAPI plus the service-binding model is CF's config and credential distribution mechanism | Re-implement. A Dapr Component (a state store, a pub/sub broker) is conceptually a CF service binding: an operator-provisioned backing service, scoped to a space, surfaced to the app as config. `scopes:` on a Component is roughly "which apps is this bound to." |
| **`dapr-sidecar-injector`** — Kubernetes mutating admission webhook | **Yes** — CF sidecars (manifest `sidecars:`, Diego process co-location) | Re-implement. CF has no admission-webhook concept and doesn't need one: it already knows how to run an extra process alongside an app in the same container/network namespace. |
| **`dapr-placement-server`** — actor placement tables (Raft, consistent hashing, namespace-scoped since v1.14) | **Partially** — Diego BBS already tracks where every app instance runs; NATS already disseminates that to routers | **Genuinely open.** See the sibling idea [[dapr-aware-gorouter]] — the placement table and GoRouter's route table are arguably the same object, which may mean CF doesn't need a separate placement service at all. |
| **`dapr-scheduler-server`** — durable jobs and actor reminders (etcd-backed) | **No** — `cf run-task` is one-shot; CF has no durable scheduler, no cron primitive, no reminder store | **Adopt upstream.** This is a real gap, and the least CF-specific component — it's a scheduling service with a storage backend, with little coupling to CF's identity or routing model. |

The **workflow engine itself needs no mapping** — it runs *inside* daprd, layered on the actor
runtime, so it arrives with the sidecar rather than as a control-plane component to host.

The rough shape of the answer: CF re-implements or bridges the components where it already has
a stronger, more CF-native primitive (identity, config distribution, process co-location),
adopts upstream where it has a genuine gap (durable scheduling), and treats actor placement as
the one genuinely open architectural question.

## Where RFC-0055 fits

Dapr's actor-to-actor and service invocation is sidecar-to-sidecar mTLS over Dapr's own mesh.
[RFC-0055 (Identity-Aware Routing for GoRouter)](https://github.com/cloudfoundry/community/blob/main/toc/rfc/rfc-0055-identity-aware-routing-for-gorouter.md)
gives CF the same guarantees at the HTTP layer, using primitives CF already has:

- per-domain mTLS on `*.apps.identity`, so only CF workloads can connect;
- caller identity extracted directly from the Diego instance identity certificate
  (`OU=app:`/`OU=space:`/`OU=organization:`), the same fields Dapr's identity model needs;
- default-deny route policies enforced by the platform, expressed per route.

So actor invocation could ride CF's identity-aware routing rather than standing up a parallel
Dapr mTLS mesh — inheriting GoRouter's load balancing, retries, access logging, and
observability for free, and inheriting platform-enforced authorization rather than
reimplementing Dapr's own ACLs.

RFC-0055 also explicitly reserves a `spiffe:` prefix in its route-policy source namespace
(alongside `cf:app:`, `cf:space:`, `cf:org:`) for future identity types. That is a natural hook
for expressing Dapr workload identities in route policies without inventing new syntax.

## Two possible developer surfaces

**Option A — manifest flag, platform-injected sidecar.**

```yaml
applications:
  - name: my-agent
    dapr:
      enabled: true
```

The platform runs `daprd` alongside the app process; the app talks to `localhost:3500`.

*For:* mirrors the annotation-driven model Dapr users already know, so existing Dapr apps and
SDKs work unmodified; one flag turns on all building blocks at once; the sidecar can be kept
patched by the platform rather than by each developer.
*Against:* introduces a runtime concept ("Dapr mode") that doesn't map onto anything else in
CF's manifest vocabulary; unclear how an operator restricts *which* building blocks are
available, or meters their use.

**Option B — service binding.**

```
cf bind-service my-agent dapr-workflow
```

*For:* fits CF's existing mental model exactly — durable execution becomes a bindable backing
service like any database, with the marketplace, plan, and quota machinery that comes with it;
operators get natural per-plan control over which capabilities a space can use; the
service-binding model is already how CF injects config and credentials, which is exactly what a
Dapr Component is.
*Against:* one sidecar serving several bound Dapr capabilities makes the "one binding, one
service instance" model a bit of a fiction; developers used to upstream Dapr would find the
onboarding unfamiliar.

These aren't mutually exclusive — a manifest flag could control *whether* the sidecar runs,
while bindings control *which components* it's configured with. That combination is probably
worth exploring over either in isolation.

## Three broader adoption strategies

1. **Dapr API surface, CF-native control plane.** Adopt `daprd` as-is for its polyglot
   building-block APIs; re-implement or bridge control-plane functions onto existing CF
   components. CF apps get Dapr's APIs and ecosystem components without CF operating Dapr's
   control plane. Most CF-native, most integration work, and creates a maintenance
   relationship with upstream's sidecar↔control-plane protocol.
2. **Adopt upstream wholesale, integrate at the edges.** Ship the full Dapr control plane as a
   BOSH release next to CF and bridge only where it touches CF — e.g. teach `dapr-sentry` to
   trust the Diego instance identity CA, and derive the Dapr namespace from org/space. Least
   re-implementation, fastest to a working prototype, but adds real operational surface
   (Raft placement cluster, etcd-backed scheduler) and a second identity system to reason about.
3. **Borrow the ideas, not the code.** Define CF-native durable-execution APIs shaped entirely
   by CF primitives, with no `daprd` dependency. Maximum coherence with the rest of CF, but
   forfeits Dapr's component ecosystem, SDKs, and the agent frameworks already building on it
   (see `dapr-agents.md`), and means CF owns a workflow engine.

This idea leans toward (1) or (2), but the point of writing it down is that the per-component
analysis above is what should decide it — not a blanket "adopt" or "don't."

## Why it might matter

Every agent framework surveyed in this research set treats durable execution as a substrate to
plug in rather than something it ships: Google ADK exposes replay-safe primitives but no engine
(`google-adk.md`), the OpenAI Agents SDK relies on external Temporal/Dapr integrations
(`openai-agents-sdk.md`), and Microsoft Agent Framework binds to Azure Durable Task
(`microsoft-agent-framework.md`). If CF wants to host agentic workloads credibly, "which
durable-execution substrate do CF apps get?" is a question it will have to answer regardless of
which framework a developer picks. Dapr is the only candidate that is CNCF-graduated,
polyglot, sidecar-delivered (so it doesn't constrain the app's language or framework), and
already has an agent framework built on it.

The secondary payoff is that most of what Dapr's control plane does, CF already does — just
under different names. Making that mapping explicit is useful even if CF never ships Dapr.

## What to research next

- Can `dapr-sentry` be configured to trust an externally-issued workload certificate (the
  Diego instance identity cert) rather than minting its own, or would this require upstream
  changes? This determines whether strategy (2) is a config exercise or a fork.
- What exactly does the sidecar↔control-plane protocol look like, and how stable is it? A
  CF-native re-implementation of the operator or placement API takes on a compatibility burden
  proportional to how fast that protocol moves.
- Does `dapr-scheduler-server` have a hard etcd dependency, or can its storage be swapped for
  something CF already runs?
- How would a Dapr namespace derived from `<org-guid>/<space-guid>` interact with CF app
  restarts, re-pushes, and blue/green deploys — does actor identity survive them?
- What is the actual operational cost of a Raft placement cluster and an etcd-backed scheduler
  at CF foundation scale, and does that change the adopt-vs-reimplement calculus?

## Related

- Sibling idea exploring whether GoRouter could subsume actor placement entirely:
  [[dapr-aware-gorouter]].
- Research notes: `dapr.md` (building blocks, control-plane components, sidecar model),
  `dapr-agents.md` (durable agent loops on Dapr Workflows), `temporal.md` and `orleans.md`
  (alternative durable-execution and virtual-actor substrates worth comparing against).
- [RFC-0055: Identity-Aware Routing for GoRouter](https://github.com/cloudfoundry/community/blob/main/toc/rfc/rfc-0055-identity-aware-routing-for-gorouter.md)
  and [RFC-0027: Generic Per-Route Features](https://github.com/cloudfoundry/community/blob/main/toc/rfc/rfc-0027-generic-per-route-features.md).
- The sidecar assumed here is the same shape as the one in [[credential-less-agent-processes]]
  and [[localhost-only-egress-for-agents]] — worth checking whether one sidecar should serve
  all three concerns.
