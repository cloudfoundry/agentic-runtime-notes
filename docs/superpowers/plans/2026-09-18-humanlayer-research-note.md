# HumanLayer Research Note Implementation Plan

> **For agentic workers:** Execute this plan inline with validation checkpoints.

**Goal:** Add and publish a sourced research note on HumanLayer's externalized agent sessions and disposable execution model.

**Architecture:** Describe the HumanLayer API/control plane, local/remote daemons, tasks, sessions, artifacts, diffs, worktrees, and streamed events. Separate durable collaboration state from host-bound execution context, then map the thesis to CF's durable state, disposable Diego processes, identity, and event streams.

**Tech Stack:** Markdown, YAML frontmatter, Devbox, Git, GitHub CLI.

---

### Task 1: Write `research/humanlayer.md`

- [ ] Add frontmatter with title `HumanLayer: Externalized Agent Sessions and Disposable Execution`, author `Ruben Koster (@rkoster)`, date `2026-09-18`, tags `[durable-execution, orchestration, observability-governance, ecosystem-survey]`, `cf_areas: [capi, diego, loggregator]`, `status: draft`, ratings, and HumanLayer repository/website/remote-daemon sources.
- [ ] Describe HumanLayer as a multiplayer coding-agent workspace with API, web/desktop/mobile interfaces, local/remote daemons, tasks, sessions, artifacts, plans, diffs, and worktrees.
- [ ] Explain the stateless-at-the-process-layer thesis: collaboration/session state and events are externalized, while daemons and agent processes can be restarted or replaced.
- [ ] Distinguish documented API event streaming and daemon reconnection from unproven live in-memory process migration between containers.
- [ ] Cover host-bound capabilities: code, tools, credentials, private services, worktrees, filesystem, and persistent daemon authentication storage.
- [ ] Assess CF relevance for CAPI/Diego, durable state stores, disposable processes, session ownership, identity, workspace persistence, and Loggregator.
- [ ] Add open questions about process migration, state completeness, worktree portability, credential rehydration, event ordering, and failure recovery.

### Task 2: Validate and publish

- [ ] Run `devbox run validate`, `devbox run test`, and `git diff --check`.
- [ ] Stage only the note and approved spec/plan, commit `docs: add HumanLayer research note`, push `research/humanlayer`, and open a checklist-complete PR targeting `main`.
- [ ] Verify PR metadata and CI with `gh pr view`.
