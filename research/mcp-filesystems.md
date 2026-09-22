---
title: "MCP Filesystems: Bidirectional Resources for Agent Workflows"
author: Ruben Koster (@rkoster)
date: 2026-09-17
tags: [orchestration, durable-execution, inter-agent-comms, ecosystem-survey]
cf_areas: [capi, diego]
status: draft
ratings:
  platform-impact:
    value: 78
    note: "Bidirectional resources could provide a standard workspace and artifact boundary for agents without coupling applications to one filesystem implementation."
  maturity:
    value: 38
    note: "The Filesystems Working Group is early-stage and lists its main Extensions Track SEP as ideating rather than finalized."
  novelty:
    value: 72
    note: "The proposal extends MCP Resources from read-oriented content to coordinated writes with concurrency and cache semantics."
  actionability:
    value: 68
    note: "The operations map to CF object storage, volumes, and workspaces, but URI, authorization, conflict, and tenant semantics remain open."
sources:
  - https://modelcontextprotocol.io/community/working-groups/filesystems
  - https://modelcontextprotocol.io/specification/latest/server/resources
  - https://github.com/modelcontextprotocol/modelcontextprotocol/pull/2571
  - https://github.com/modelcontextprotocol/modelcontextprotocol/pull/2532
  - https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1708
  - https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem
---

## Summary

The MCP Filesystems Working Group is exploring how to make MCP Resources bidirectional so an
agent can write results back to the service it reads from. Its proposed Extensions Track SEP
would define create, update, delete, and metadata-stat operations, optimistic concurrency, and
the interaction between writes, change notifications, and caching. The work is early-stage,
with the charter listing the primary SEP as ideating; for Cloud Foundry it is a potential
protocol boundary for agent workspaces and artifacts, not a filesystem mounting standard.

## Key findings

- **The group extends Resources rather than creating a parallel `files/*` primitive.** MCP
  Resources already represent content by URI and include a `file://` scheme for resources that
  behave like a filesystem. The Filesystems WG intends to make that existing surface writable.
- **The proposed operations cover basic resource lifecycle.** The charter identifies create,
  update, delete, and `stat`. The metadata read would answer existence, size, and last-modified
  information without fetching the resource body.
- **Optimistic concurrency is a core requirement.** The proposal must specify how two writers
  avoid lost updates and how a client creates a resource under a create-if-absent precondition.
  This implies version, etag, or equivalent precondition semantics even where the final wire
  representation is not yet settled.
- **Writes affect notifications and caches.** The group plans to reconcile writes with
  `notifications/resources/updated`, cache TTL and scope fields such as `ttlMs` and
  `cacheScope`, and `lastModified` annotations. A write therefore changes both storage state
  and how clients decide whether their local view is fresh.
- **Host filesystem behavior is deliberately separate.** The charter leaves host-side sandbox
  and local-disk semantics out of scope. The WG is standardizing client/server wire behavior;
  how an AI host materializes a URI into a local workspace remains a host concern.
- **Authorization is not being redesigned by this group.** The charter leaves write policy to
  the existing MCP authorization specification and server/application policy. A server still
  needs to decide which identity can create, update, or delete a resource.
- **Adjacent proposals expose the design space.** The charter references resource submission
  for agent coordination, binary resource streaming, and a prior client-brokered filesystem
  proposal. These efforts raise related questions about writes, binary content, transport, and
  whether resource operations should be tools or protocol methods.
- **The work is not yet a finished standard.** The charter identifies the main Filesystem
  Operations for Resources SEP as ideating and describes a biweekly working session with
  provisional cadence. Implementers should expect proposal changes.
- **The reference filesystem server is a useful contrast.** Existing filesystem servers can
  expose a configured local directory through tools, but that deployment model does not by
  itself define remote resource write semantics, optimistic concurrency, or cross-client cache
  invalidation.

## CF relevance

Cloud Foundry could use bidirectional MCP Resources as a portable boundary for agent workspaces,
build artifacts, reports, and durable task outputs. A CF-hosted agent might read a resource from
an object store or service and write a result back through the MCP server, while CAPI-managed
application metadata, service bindings, and platform policy remain outside the resource format.
The backing implementation could use S3-compatible object storage, a volume service, a database,
or an application-specific workspace rather than assuming local disk.

The proposal's concurrency semantics are especially relevant to multi-instance agents. Diego
may run or replace multiple processes, and several agents or tools may update the same artifact.
Version preconditions, conflict responses, idempotent retries, and explicit ownership would be
needed to avoid silent lost updates. Cache metadata and resource notifications could help clients
avoid stale workspace views, but the platform would need to correlate resource changes with
application, space, agent, and audit identities.

The protocol does not solve CF authorization or sandboxing by itself. A gateway or MCP server
would need to enforce space/org policy, validate bindings and workload identity, restrict URI
namespaces, and audit writes. Host-side materialization also remains a separate choice: CF could
provide a bound remote workspace, a mounted volume, or an application-managed projection, each
with different isolation and lifecycle properties.

## Open questions

- What URI namespace and tenant model should a CF-backed resource service use for orgs, spaces,
  applications, agent sessions, and shared artifacts?
- Which version token or precondition semantics should CF expose for concurrent updates, and how
  should clients resolve conflicts after retries or process replacement?
- Can object storage, volume services, and application workspaces share one MCP resource model
  without hiding important atomicity and durability differences?
- How should resource notifications, TTLs, cache scopes, and `lastModified` map to CF event
  streams and client reconnect behavior?
- Which component authorizes resource writes, and how should user, application, agent, and
  delegated tool identities be combined?
- What isolation and redaction controls are needed when resource contents contain prompts,
  credentials, source code, or tenant data?
- Should CF provide a standard remote workspace service, or leave resource semantics to MCP
  servers and application teams?
