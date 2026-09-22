# SpiceDB Research Note Implementation Plan

> **For agentic workers:** Execute this plan inline with validation checkpoints.

**Goal:** Add and publish a sourced research note on SpiceDB as a fine-grained authorization substrate for agents and Cloud Foundry resources.

**Architecture:** Describe SpiceDB's schema, relationship, permission-check, consistency, and datastore/API model. Then analyze a CF integration boundary where an external certificate-verifying component maps instance identities to stable SpiceDB subjects and applications ask SpiceDB for authorization decisions.

**Tech Stack:** Markdown, YAML frontmatter, Devbox, Git, GitHub CLI.

---

### Task 1: Write the SpiceDB research note

**Files:**
- Create: `research/spicedb.md`

- [ ] Add frontmatter with title `SpiceDB: Fine-Grained Authorization for Agents and Cloud Foundry`, author `Ruben Koster (@rkoster)`, date `2026-09-17`, tags `[authorization, identity, agent-runtime, ecosystem-survey]`, `cf_areas: [uaa, capi, diego]`, `status: draft`, provisional ratings, and links to SpiceDB's repository, README, concepts, modeling, consistency, API, and Zanzibar sources.
- [ ] Explain SpiceDB as a Zanzibar-inspired authorization database where schemas define relations and permissions, relationship tuples store facts, and clients issue checks or reverse lookups.
- [ ] Cover consistency choices, caveated relationships, schema validation/tooling, supported datastores, gRPC/HTTP APIs, and the separation between authentication and authorization.
- [ ] Explain agent/tool examples: an agent instance requesting access to a CF space, app, route, service binding, or tool, with relations representing ownership, delegation, membership, and environment boundaries.
- [ ] Describe a proposed CF boundary where a gateway or policy service verifies an instance identity certificate, maps its verified identity to a stable subject, and queries SpiceDB; do not claim native certificate validation in SpiceDB.
- [ ] Assess relationship synchronization from CAPI/Diego events, certificate rotation and revocation, latency/availability, tenant isolation, fail-open/fail-closed behavior, and auditability.
- [ ] Add open questions around canonical subject IDs, delegated agent authority, stale tuples, revocation timing, policy ownership, and operational placement.

### Task 2: Validate and inspect

**Files:**
- Test: `.github/scripts/validate_notes.py`

- [ ] Run `devbox run validate` and expect all research notes and ideas to be valid.
- [ ] Run `devbox run test` and expect success.
- [ ] Run `git diff --check` and inspect `git status --short`; leave unrelated environment artifacts unstaged.

### Task 3: Commit and publish

**Files:**
- Include: `research/spicedb.md`
- Include: `docs/superpowers/specs/2026-09-17-spicedb-research-note-design.md`
- Include: `docs/superpowers/plans/2026-09-17-spicedb-research-note.md`

- [ ] Stage only the three intended files, using `git add -f` for ignored planning artifacts.
- [ ] Commit with `docs: add SpiceDB research note`.
- [ ] Push `research/spicedb` to origin.
- [ ] Open a PR titled `docs: add SpiceDB research note` targeting `main`, with the repository checklist completed.
- [ ] Verify the PR URL, branch, state, and CI status with `gh pr view`.
