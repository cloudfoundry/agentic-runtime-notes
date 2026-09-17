---
title: "SpiceDB: Fine-Grained Authorization for Agents and Cloud Foundry"
author: Ruben Koster (@rkoster)
date: 2026-09-17
tags: [authorization, identity, agent-runtime, ecosystem-survey]
cf_areas: [uaa, capi, diego]
status: draft
ratings:
  platform-impact:
    value: 84
    note: "Centralized relationship-based authorization could give agents and tools consistent access decisions across CF spaces, apps, and services."
  maturity:
    value: 82
    note: "SpiceDB is a mature, actively maintained Zanzibar-inspired authorization system with production use claims, multiple datastores, and client APIs."
  novelty:
    value: 62
    note: "The core model follows Zanzibar, while caveats and reverse lookups make it a practical foundation for complex agent and platform authorization."
  actionability:
    value: 80
    note: "The schema and tuple model provides a concrete way to prototype agent identity and delegated access policies, subject to CF identity integration work."
sources:
  - https://github.com/authzed/spicedb
  - https://raw.githubusercontent.com/authzed/spicedb/main/README.md
  - https://authzed.com/docs/spicedb/concepts/schema
  - https://authzed.com/docs/spicedb/concepts/consistency
  - https://authzed.com/docs/spicedb/modeling/relationship-based-access-control
  - https://authzed.com/docs/spicedb/modeling/caveats
  - https://authzed.com/docs/spicedb/api/grpc
  - https://research.google/pubs/zanzibar-googles-consistent-global-authorization-system/
---

## Summary

SpiceDB is an open-source, Zanzibar-inspired database for storing and querying fine-grained
authorization relationships. Applications define a schema, write relationship tuples, and
ask SpiceDB whether a subject has a permission on a resource; reverse lookups answer questions
such as who can access a resource or what a subject can do. For Cloud Foundry agent workloads,
SpiceDB is a candidate authorization substrate for agent-to-tool and agent-to-platform access,
but an external component would still need to authenticate instance identity certificates and
map them to stable authorization subjects.

## Key findings

- **SpiceDB separates authorization from authentication.** Its focus is evaluating whether a
  subject may perform an action. The project is intentionally agnostic to authentication
  systems and identity providers, which leaves certificate verification and identity lifecycle
  to a gateway, application, or platform identity service.
- **Schemas describe the authorization graph.** Developers define resource types, relations,
  and permissions. Relationship data then connects subjects to resources, while permissions
  compute allowed actions through direct relations, unions, intersections, exclusions, and
  traversals through related resources.
- **The data model fits platform hierarchies.** A schema can represent subjects such as users,
  service accounts, agent instances, groups, spaces, applications, routes, tools, and service
  bindings. A permission can inherit through relationships, for example an agent authorized
  for a space receiving a narrower or broader permission on applications within that space.
- **Checks are designed for distributed authorization.** Clients can issue permission checks
  and other queries through gRPC, HTTP, or client libraries. SpiceDB exposes consistency choices
  so callers can trade freshness and latency according to the risk of using a recently changed
  relationship.
- **Caveated relationships add contextual conditions.** Caveats can attach additional
  expression-based conditions to relationships, combining relationship-based access control
  with request context. This is potentially useful for agent policies that depend on a
  deployment, environment, time window, or other request attributes, but the platform must
  define which context is trusted and how it is supplied.
- **Reverse lookups are useful for control and audit workflows.** In addition to asking whether
  an agent can access a resource, callers can query which subjects have a permission or what
  resources a subject can access. These queries can support authorization review, tool catalog
  filtering, and incident investigation, subject to query cost and privacy controls.
- **SpiceDB supports external durable datastores.** The project documents support for systems
  including PostgreSQL, CockroachDB, MySQL, and Google Cloud Spanner. This lets operators choose
  a persistence and availability architecture separately from the authorization API, but makes
  datastore migration, consistency, backups, and schema/tuple rollout operational concerns.
- **An agent identity boundary is required for CF.** A possible CF design would have a gateway
  or policy service validate an instance identity certificate, establish the workload's trusted
  identity, and map it to a stable SpiceDB subject such as `agent_instance:<guid>`. SpiceDB
  would then evaluate the subject's relationships. This is a proposed integration boundary;
  SpiceDB itself should not be assumed to validate CF instance identity certificates.
- **Relationship data would need lifecycle synchronization.** CAPI, Diego, UAA, service
  brokers, or another platform source could publish changes such as space membership, app
  ownership, binding creation, instance replacement, and revocation. Tuple freshness becomes a
  security property: stale grants can outlive a certificate or application lifecycle event.
- **SpiceDB is an authorization service, not an agent runtime.** It does not execute agents,
  issue identity certificates, manage CF application lifecycle, or replace network policy. It
  can provide a decision point that agent runtimes, tool gateways, and platform APIs call.

## CF relevance

Cloud Foundry could use SpiceDB as a shared fine-grained authorization service for agentic
workloads. An agent instance might present its CF instance identity certificate to a gateway;
the gateway would validate the certificate and bind the request to a stable workload identity.
The gateway or application would then ask SpiceDB whether that identity may invoke a tool,
read a service binding, access an application, or operate on a resource in a particular space.
This separates proof of identity from policy evaluation and avoids distributing a large,
platform-wide authorization graph into every agent process.

The same model could express delegation: a platform-managed agent controller may be allowed to
create or operate on agents in a space, while an individual agent receives only the permissions
needed for its task. Relations could connect an agent instance to a deployment, app, space,
organization, tool, or service binding, with caveats supplying bounded context such as an
environment or expiration condition. The exact schema would be a CF design decision, not an
existing SpiceDB integration.

Operating this as a platform capability would require a reliable relationship ingestion path.
CAPI and Diego events could update tuples as applications, instances, spaces, bindings, and
routes change. Certificate rotation and instance replacement would need stable subject and
revocation semantics so that a new instance does not accidentally inherit an old instance's
authority. Operators would also need to choose fail-closed behavior for security-sensitive
actions, bounded caching for availability, and audit correlation between the certificate,
SpiceDB subject, authorization decision, and resulting platform operation.

## Open questions

- What is the canonical SpiceDB subject for a CF agent: application, process instance,
  instance identity certificate, service account, or a composite of these?
- Which component should verify CF instance identity certificates and perform the mapping to
  SpiceDB subjects, and how should certificate rotation and revocation invalidate authority?
- Which CAPI, Diego, UAA, broker, and routing events must update relationships, and what tuple
  staleness is acceptable for each permission class?
- How should delegated agent authority be represented without allowing an agent to mint or
  transfer permissions beyond its own grant?
- Which agent-to-tool and agent-to-resource checks need caveats, and which request context can
  be trusted by the authorization service?
- What should happen when SpiceDB is unavailable or a consistency requirement cannot be met:
  fail closed, use a bounded cached decision, or permit only a restricted operation set?
- How should authorization decisions, relationship writes, certificate identities, and CF
  audit events be correlated without exposing sensitive policy data?
- Should each CF foundation run a shared SpiceDB service, or should authorization be isolated
  per foundation, org, space, or agent platform?
