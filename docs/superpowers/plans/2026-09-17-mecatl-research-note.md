# Mecatl Research Note Implementation Plan

> **For agentic workers:** Execute this plan inline with validation checkpoints.

**Goal:** Add and publish a sourced research note on Mecatl as a cloud-native production agent harness.

**Architecture:** Describe the provider-agnostic agent loop, tools/permissions/delegation, durable sessions and event logs, and the Kubernetes `mecak8s` reference runtime. Map the generic engine and Kubernetes deployment separately to CF lifecycle, identity, bindings, draining, and observability.

**Tech Stack:** Markdown, YAML frontmatter, Devbox, Git, GitHub CLI.

---

### Task 1: Write `research/mecatl.md`

- [ ] Add frontmatter with title `Mecatl: Cloud-Native Agent Harness with Durable State and Permissions`, author `Ruben Koster (@rkoster)`, date `2026-09-17`, tags `[orchestration, durable-execution, authorization, observability-governance]`, `cf_areas: [uaa, capi, diego, loggregator]`, `status: draft`, ratings, and Mecatl repository/README/docs sources.
- [ ] Explain the streaming provider-agnostic loop, tools, skills, hooks, subagents, teams, compaction, and service boundaries.
- [ ] Cover deny-dominant permissions, approval flows, secret-scrubbed environments, attribution, audit, and narrowing delegated capabilities.
- [ ] Cover durable sessions and append-only event logs, gRPC/HTTP-SSE/TypeScript clients, and the distinction between embedded engine and `mecak8s` runtime.
- [ ] Describe Redis-backed state, Kubernetes session leases, one-writer coordination, drain handling, and disposable replicas.
- [ ] Assess CF relevance for CAPI/Diego replacement, UAA identity, service bindings, external Redis/state stores, draining, and Loggregator.
- [ ] Add open questions about durable session ownership, permissions, delegation, failover, provider credentials, audit, and running without Kubernetes leases.

### Task 2: Validate and publish

- [ ] Run `devbox run validate`, `devbox run test`, and `git diff --check`.
- [ ] Stage only the note and approved spec/plan, commit `docs: add Mecatl research note`, push `research/mecatl`, and open a checklist-complete PR targeting `main`.
- [ ] Verify PR metadata and CI with `gh pr view`.
