# Obot Research Note Implementation Plan

> **For agentic workers:** Execute this plan inline with validation checkpoints.

**Goal:** Add and publish a sourced research note on Obot as a governed AI platform for gateways, registries, hosted agents, policy, and audit.

**Architecture:** Describe Obot's platform as a set of cooperating planes: MCP/LLM gateways, hosted sandbox execution, identity and policy services, registries, and user-device controls. Map those planes to Cloud Foundry services and identify where Diego, CAPI, routing, isolation, and Loggregator would need extensions.

**Tech Stack:** Markdown, YAML frontmatter, Devbox, Git, GitHub CLI.

---

### Task 1: Write the Obot research note

**Files:**
- Create: `research/obot.md`

- [ ] Add frontmatter with title `Obot: Governed AI Gateways, Registries, and Hosted Agents`, author `Ruben Koster (@rkoster)`, date `2026-09-17`, tags `[governance, authorization, agent-runtime, ecosystem-survey]`, `cf_areas: [uaa, capi, diego, loggregator]`, `status: draft`, provisional ratings, and Obot repository/README sources.
- [ ] Describe the MCP Gateway as a governed entry point with proxying, composite servers, per-identity access, OAuth/credentials, secret bindings, and request/response filters.
- [ ] Describe the LLM Gateway as provider-compatible access with centrally managed credentials, scoped client keys, model access policies, token/cost recording, and request/response metadata.
- [ ] Describe hosted MCP servers and agents, Docker/Kubernetes sandbox execution, domain egress policy, and the security trade-off of mounting a Docker socket for development.
- [ ] Describe Obot Sentry, CLI, Git-backed MCP/Skills catalogs, registry APIs, identity providers, permissions, secrets, and correlated audit logs.
- [ ] Assess CF relevance as a shared gateway/registry/policy service, with service bindings for credentials/endpoints, Diego or an external sandbox substrate for hosted workloads, CAPI lifecycle integration, and Loggregator-compatible audit correlation.
- [ ] Add open questions about tenant isolation, platform versus application ownership, sandboxing, egress policy, credential rotation, catalog governance, and audit data boundaries.

### Task 2: Validate and inspect

**Files:**
- Test: `.github/scripts/validate_notes.py`

- [ ] Run `devbox run validate` and expect all research notes and ideas to be valid.
- [ ] Run `devbox run test` and expect success.
- [ ] Run `git diff --check` and inspect `git status --short`; leave unrelated environment artifacts unstaged.

### Task 3: Commit and publish

**Files:**
- Include: `research/obot.md`
- Include: `docs/superpowers/specs/2026-09-17-obot-research-note-design.md`
- Include: `docs/superpowers/plans/2026-09-17-obot-research-note.md`

- [ ] Stage only the three intended files, using `git add -f` for ignored planning artifacts.
- [ ] Commit with `docs: add Obot research note`.
- [ ] Push `research/obot` to origin.
- [ ] Open a PR titled `docs: add Obot research note` targeting `main`, with the repository checklist completed.
- [ ] Verify the PR URL, branch, state, and CI status with `gh pr view`.
