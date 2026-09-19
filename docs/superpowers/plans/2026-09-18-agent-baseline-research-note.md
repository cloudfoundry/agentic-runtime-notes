# Agent Baseline Research Note Implementation Plan

> **For agentic workers:** Execute this plan inline with validation checkpoints.

**Goal:** Add and publish a sourced research note on Agent Baseline's six security outcomes and 35 controls.

**Architecture:** Present Agent Baseline as an outcome/control/evidence framework, then map Discover, Constrain, Authorize, Observe, Validate, and Respond to CF platform primitives and agent-specific gaps.

**Tech Stack:** Markdown, YAML frontmatter, Devbox, Git, GitHub CLI.

---

### Task 1: Write `research/agent-baseline.md`

- [ ] Add frontmatter with title `Agent Baseline: Six Security Outcomes for Enterprise AI Agents`, author `Ruben Koster (@rkoster)`, date `2026-09-18`, tags `[authorization, sandboxing, observability-governance, ecosystem-survey]`, `cf_areas: [uaa, capi, diego, loggregator]`, `status: draft`, provisional ratings, and Agent Baseline website/source/white-paper links.
- [ ] Explain the threat model: runtime-programmable agents with access to data, tools, and systems, where mistaken or malicious instructions can cause actions before human intervention.
- [ ] Describe all six outcomes and the evidence-oriented nature of the 35 controls.
- [ ] Map Discover and Constrain to CF inventory, lifecycle, isolation, networking, and credential capabilities.
- [ ] Map Authorize and Observe to UAA/workload identity, policy, action attribution, Loggregator, and audit/provenance.
- [ ] Map Validate and Respond to build/release admission, evaluation, drift checks, revocation, quarantine, evidence preservation, and incident response.
- [ ] State that Agent Baseline is a working draft for public comment, not a finalized standard, and add open questions about control ownership, evidence, tenancy, and platform gaps.

### Task 2: Validate and publish

- [ ] Run `devbox run validate`, `devbox run test`, and `git diff --check`.
- [ ] Stage only the note and approved spec/plan, commit `docs: add Agent Baseline research note`, push `research/agent-baseline`, and open a checklist-complete PR targeting `main`.
- [ ] Verify PR metadata and CI with `gh pr view`.
