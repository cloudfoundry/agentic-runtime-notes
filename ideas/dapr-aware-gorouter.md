---
title: Dapr-aware GoRouter — routing to the instance where the work lives
author: Ruben Koster (@rkoster)
date: 2026-08-11
tags: [inter-agent-comms, runtime-lifecycle, orchestration]
ratings:
  platform-impact:
    value: 50
    note: 'GoRouter already has instance-addressed routing, endpoint metadata, and NATS updates, but it cannot resolve an actor ID to the instance that currently owns the work.'
  maturity:
    value: 50
    note: 'Dapr placement and CF routing are production-capable ingredients, but no implementation or operational evidence demonstrates actor-to-instance resolution through GoRouter or safe behavior during placement migration.'
  novelty:
    value: 75
    note: 'Making a PaaS edge router consume or replace a virtual-actor placement table is an emerging combination, especially with authenticated actor-addressed routing through RFC-0055.'
  actionability:
    value: 75
    note: 'The shallow design bounds an experiment to daprd placement lookup plus X-CF-APP-INSTANCE, with explicit checks for host-to-index mapping, header propagation, and migration correctness.'

---

## The idea

GoRouter today assumes app instances are interchangeable: a request for `my-app.example.com`
can go to any healthy instance, and load balancing picks one. Durable-execution workloads break
that assumption. A Dapr actor — and therefore a Dapr workflow, which is built on actors — is
**single-threaded and stateful, and lives on exactly one instance at a time**. A call for actor
`order-123` must reach *that* instance; any other instance is not a valid backend, and routing
there either fails or, worse, double-activates the actor.

Dapr solves this with `dapr-placement-server`: a Raft-backed service that disseminates a
consistent-hash table so every sidecar can compute which host owns a given actor, then makes a
direct sidecar-to-sidecar call.

The observation worth exploring: **Dapr's placement table and GoRouter's route table are the
same kind of object.** Both map a logical identity to a set of backend instances. Both are
disseminated over NATS. Both must react to instances appearing, disappearing, and being
rebalanced. CF already runs this machinery — route-emitter watches Diego BBS and publishes
endpoint updates (carrying per-endpoint `instance_id`, `space_id`, and `organization_id` tags)
over NATS to every GoRouter.

CF also already has a direct-to-instance routing primitive in
`X-CF-APP-INSTANCE: <app-guid>:<index>`, plus instance affinity via the `__VCAP_ID__` sticky
session cookie. The building blocks for "route to a specific instance, not just any instance"
are present today; what's missing is a way to decide *which* instance based on where a unit of
durable work currently lives.

## Three depths, as a progression

**1. Shallow — daprd resolves placement, GoRouter honours `X-CF-APP-INSTANCE`.**

The sidecar does the placement lookup exactly as it does today, then instead of opening a
direct mesh connection it issues an ordinary HTTP request with
`X-CF-APP-INSTANCE: <app-guid>:<index>`.

**GoRouter needs no changes at all.** Actor and workflow traffic immediately gains GoRouter's
load balancing for non-actor calls, retries, access logging, and — combined with
[RFC-0055](https://github.com/cloudfoundry/community/blob/main/toc/rfc/rfc-0055-identity-aware-routing-for-gorouter.md)
— platform-enforced, default-deny route policies on authenticated caller identity. Dapr's
own mTLS mesh becomes redundant on CF, because CF's identity-aware routing already provides
mutual authentication between workloads using the certs CF already issues.

The open detail is mapping Dapr's placement output (a host, in Dapr's model) onto a CF instance
index, and keeping that mapping correct as instances move.

**2. Medium — GoRouter learns placement and resolves actor IDs itself.**

GoRouter subscribes to actor placement state over the same NATS bus it already uses for route
updates, and resolves the target instance directly from the standard Dapr invocation path:

```
/v1.0/actors/{actorType}/{actorId}/method/{method}
```

Opt-in per route via the route options framework from
[RFC-0027](https://github.com/cloudfoundry/community/blob/main/toc/rfc/rfc-0027-generic-per-route-features.md),
so only routes explicitly marked as actor-addressed pay the cost.

The payoff: **actor invocation stops requiring a Dapr sidecar on the calling side.** Any HTTP
client — another CF app, a CF task, an external partner over an mTLS domain — can address an
actor by ID and reach the right instance. That is a meaningfully more open model than a
sidecar-only mesh, and it composes with RFC-0055 so the caller is authenticated and authorized
by the platform on the way in.

**3. Deep — GoRouter's route table *is* the placement table.**

If GoRouter already knows every instance of every app (it does), and already receives churn
updates over NATS (it does), and can already route to a specific instance (it can), then
`dapr-placement-server` may be redundant on CF. One source of truth for "where are the
instances," shared between routing and placement, maintained by machinery CF already operates.

This would directly answer the open question left in the sibling idea
[[dapr-durable-execution-on-cf]]: placement is the one control-plane component where CF's
existing primitives *nearly* cover Dapr's, and this is what closing that gap would look like.

## Why CF is unusually well-positioned

- **route-emitter already carries the right metadata.** Per-endpoint `instance_id`,
  `space_id`, and `organization_id` tags are already in GoRouter's route table — the same
  fields a namespaced Dapr placement table needs, given that a Dapr namespace maps naturally
  onto a CF org/space combination.
- **NATS is already the dissemination bus.** Dapr's placement service and CF's route-emitter
  are solving the same distribution problem with different infrastructure; CF would be reusing
  a bus it already runs and operates at scale.
- **RFC-0055 supplies authenticated caller identity.** Composing placement-aware routing with
  identity-aware routing gives *authenticated, actor-addressed routing* — the caller is proven
  to be a specific CF app, and the request lands on the specific instance owning that actor.
  Neither Dapr nor CF provides that combination on its own today.
- **Instance-addressed routing already exists.** `X-CF-APP-INSTANCE` and `__VCAP_ID__` mean
  GoRouter is not being asked to do something structurally new — only to decide the target
  instance from a different input.

## The hard part

**Actor placement needs consensus; GoRouter's route table is eventually consistent.** Dapr
uses Raft for placement precisely because two sidecars disagreeing about who owns actor
`order-123` means double activation — two instances of a single-threaded, stateful entity
running concurrently, which is a correctness failure, not a performance one. GoRouter's route
table is eventually consistent and maintained per router instance; during convergence after a
scale event, two GoRouters could legitimately disagree.

The safe mitigation is to keep **the sidecar authoritative**: GoRouter's placement knowledge is
a routing optimization, and the receiving sidecar still validates that it actually owns the
requested actor, rejecting or forwarding if not. That preserves correctness while still
capturing most of the benefit, and it's the design any of the three depths should probably
assume until proven unnecessary.

Other unresolved pieces:

- **Rebalancing on scale events.** Consistent hashing means scaling an app reshuffles actor
  ownership. Actors must be deactivated and reactivated elsewhere, with in-flight work drained.
  CF's existing scale/rebalance flows have no notion of this today.
- **Where the hash ring lives.** Should GoRouter hold the ring and compute placement itself, or
  receive already-resolved mappings? The former scales better and matches Dapr's design; the
  latter keeps GoRouter simpler and the logic in one place.
- **Blast radius and cost.** Actor placement state is far more volatile than route state.
  Whether GoRouter should carry that churn — or whether it degrades routing for ordinary apps
  sharing the same routers — needs measurement, not speculation.
- **Failure semantics.** What should GoRouter return when an actor's owning instance is
  unreachable or mid-migration? A 503 is wrong if the actor is simply moving; retry-with-
  backoff against a re-resolved target is probably right, but that's a behaviour change.

## Why it might matter

CF's routing tier is one of its strongest, most battle-tested assets, and it is currently
unusable for any workload where instances aren't interchangeable. That excludes essentially all
durable-execution and stateful-agent workloads — exactly the shape agentic applications take.
Teaching GoRouter to route by *where the work lives* rather than *which instance is free* would
extend CF's best-in-class routing to a workload class it can't serve today, using
infrastructure CF already runs.

It would also mean CF could offer Dapr's durable-execution APIs without operating Dapr's
placement service — reducing the operational surface of the adoption path sketched in
[[dapr-durable-execution-on-cf]] to the one component CF genuinely lacks (durable scheduling).

## What to research next

- How exactly does Dapr disseminate placement — full hash ring to every sidecar, or resolved
  mappings? Is the format stable enough for a non-Dapr consumer like GoRouter to depend on?
- What is the actual update frequency and payload size of placement state at realistic actor
  counts, and how does that compare to route-table churn GoRouter handles today?
- Could this be prototyped as a GoRouter plugin or a route-option handler rather than core
  routing changes, to de-risk the medium depth?
- Does `X-CF-APP-INSTANCE` survive the full request path (load balancer → GoRouter → Envoy →
  app) intact, and is it safe to have a sidecar set it, given it can currently be set by any
  client with the app GUID?
- Is there prior art in other platforms for consensus-free actor placement — or is Raft (or
  equivalent) simply the price of correctness here?

## Related

- Sibling idea this splits out from: [[dapr-durable-execution-on-cf]] — the control-plane
  mapping that leaves actor placement as its one genuinely open question.
- [RFC-0055: Identity-Aware Routing for GoRouter](https://github.com/cloudfoundry/community/blob/main/toc/rfc/rfc-0055-identity-aware-routing-for-gorouter.md)
  (per-domain mTLS, identity extraction from instance identity certs, default-deny route
  policies) and [RFC-0027: Generic Per-Route Features](https://github.com/cloudfoundry/community/blob/main/toc/rfc/rfc-0027-generic-per-route-features.md)
  (the route-options framework a per-route opt-in would build on).
- Research notes: `dapr.md` (placement service, actor model), `orleans.md` (the virtual-actor
  model Dapr's actors derive from, including its grain directory — a directly comparable
  design for the consistency problem above), `dapr-agents.md` (why actor placement matters for
  agent workloads specifically).
