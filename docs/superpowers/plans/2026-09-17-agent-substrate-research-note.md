# Agent Substrate Research Note Implementation Plan

> **For agentic workers:** Execute this plan inline with validation checkpoints.

**Goal:** Add and publish a concise architecture-first research note on Agent Substrate and its Cloud Foundry relevance.

**Architecture:** Describe Substrate as an actor lifecycle and sandbox multiplexing layer: a control plane maps suspended actors onto ready workers, snapshots state, resumes actors on demand, and routes traffic. Separate documented demos from aspirational architecture, then map the model to CF process supervision, routing, isolation, and density.

**Tech Stack:** Markdown, YAML frontmatter, Devbox, Git, GitHub CLI.

---

### Task 1: Write the research note

**Files:**
- Create: `research/agent-substrate.md`

- [ ] Add frontmatter with title `Agent Substrate: Multiplexed Sandboxed Actors`, author `Ruben Koster (@rkoster)`, date `2026-09-17`, tags `[sandboxing, workload-isolation, orchestration, ecosystem-survey]`, `cf_areas: [diego, capi]`, `status: draft`, provisional ratings, and sources for the repository, README, architecture document, command tour, and counter demo.
- [ ] Explain the actor/worker model, where many mostly-idle actors are mapped onto fewer ready workers.
- [ ] Describe lifecycle operations: create/destroy, suspend/resume, worker assignment, routing, and full-state snapshots for process memory and filesystem state.
- [ ] Describe the component split: `ateapi` gRPC control plane, `atelet` node supervisor, `atecontroller` WorkerPool reconciler, `atenet` Envoy routing, and gVisor/microVM execution helpers.
- [ ] Distinguish the working counter demonstration from the architecture document's aspirational elements and note that the project is not an officially supported Google product.
- [ ] Assess Cloud Foundry relevance for Diego density, CAPI lifecycle APIs, route-to-resume behavior, sandbox isolation, snapshot storage, and observability.
- [ ] Add open questions about CF-native suspend/resume, trusted snapshot formats, network identity, tenant isolation, failure recovery, and whether actor multiplexing belongs in Diego or an adjacent substrate.

### Task 2: Validate and inspect

**Files:**
- Test: `.github/scripts/validate_notes.py`

- [ ] Run `devbox run validate` and expect all research notes and ideas to be valid.
- [ ] Run `devbox run test` and expect success.
- [ ] Run `git diff --check` and inspect `git status --short`; leave unrelated environment artifacts unstaged.

### Task 3: Commit and publish

**Files:**
- Include: `research/agent-substrate.md`
- Include: `docs/superpowers/specs/2026-09-17-agent-substrate-research-note-design.md`
- Include: `docs/superpowers/plans/2026-09-17-agent-substrate-research-note.md`

- [ ] Stage only the three intended files, using `git add -f` for ignored planning artifacts.
- [ ] Commit with `docs: add Agent Substrate research note`.
- [ ] Push `research/agent-substrate` to origin.
- [ ] Open a PR titled `docs: add Agent Substrate research note` targeting `main`, with the repository checklist completed.
- [ ] Verify the PR URL, branch, state, and CI status with `gh pr view`.
