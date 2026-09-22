# MCP Filesystems Research Note Implementation Plan

> **For agentic workers:** Execute this plan inline with validation checkpoints.

**Goal:** Add and publish a sourced research note on the MCP Filesystems Working Group and bidirectional Resources.

**Architecture:** Describe the proposed wire-level resource operations and concurrency/cache semantics, then distinguish them from local filesystem mounting and authorization. Map the proposal to CF-hosted agent workspaces, object storage, service bindings, and platform audit.

**Tech Stack:** Markdown, YAML frontmatter, Devbox, Git, GitHub CLI.

---

### Task 1: Write `research/mcp-filesystems.md`

- [ ] Add frontmatter with title `MCP Filesystems: Bidirectional Resources for Agent Workflows`, author `Ruben Koster (@rkoster)`, date `2026-09-17`, tags `[orchestration, durable-execution, inter-agent-comms, ecosystem-survey]`, `cf_areas: [capi, diego]`, `status: draft`, provisional ratings, and official charter/spec/SEP sources.
- [ ] Explain the working group's mission to make MCP Resources bidirectional and its early-stage/ideating status.
- [ ] Cover proposed `create`, `update`, `delete`, and `stat` operations, create-if-absent semantics, optimistic concurrency, and metadata such as existence, size, and last-modified.
- [ ] Cover change notifications, `ttlMs`, `cacheScope`, `lastModified`, and the relationship to existing resource update notifications and caching.
- [ ] Distinguish remote resource protocol semantics from host-side filesystem materialization, local disk/sandbox behavior, and authorization policy.
- [ ] Assess CF relevance for agent workspaces, blob/object stores, volumes, bindings, concurrent writers, cache invalidation, audit, and policy enforcement.
- [ ] Add open questions about URI namespaces, version tokens, conflicts, atomicity, tenant isolation, offline clients, and write authorization.

### Task 2: Validate and publish

- [ ] Run `devbox run validate`, `devbox run test`, and `git diff --check`.
- [ ] Stage only the note and approved spec/plan, commit `docs: add MCP Filesystems research note`, push `research/mcp-filesystems`, and open a checklist-complete PR targeting `main`.
- [ ] Verify PR metadata and CI with `gh pr view`.
