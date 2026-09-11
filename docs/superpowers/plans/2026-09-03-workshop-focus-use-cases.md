# Workshop Focus Use Cases Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Present two workshop-selected focus use cases above the platform primitives and let users highlight evidence by use case, primitive, or their intersection.

**Architecture:** A curated YAML file defines use-case narratives, note memberships, and primitive applicability. The generator validates and embeds this layer alongside existing primitive membership. The static page maintains independent use-case and primitive state and applies one matching predicate to markers, clusters, pickers, and dialogs.

**Tech Stack:** Python 3.12, PyYAML, unittest, generated vanilla HTML/CSS/JavaScript.

---

## Files and Responsibilities

- Create `scripts/focus_use_cases.yaml`: two workshop use cases, narratives, primitive applicability, and note memberships.
- Modify `scripts/generate_research_map.py`: use-case loading/validation, workshop-result content, cards, independent selection state, intersection filtering, status, counts, ordering, and badges.
- Modify `tests/test_generate_research_map.py`: validation, content, interaction, accessibility, escaping, and regression coverage.
- Modify `generated/research-map.html`: regenerated static workshop-results artifact.

### Task 1: Define and validate focus-use-case configuration

**Files:**
- Create: `scripts/focus_use_cases.yaml`
- Modify: `scripts/generate_research_map.py`
- Modify: `tests/test_generate_research_map.py`

- [ ] **Step 1: Write failing validation tests**

Add tests for `validate_focus_use_cases(use_cases, known_paths, primitive_ids)` covering exactly two entries, required string/list fields, unique IDs, non-empty core membership, duplicate core/supporting paths, unknown note paths, unknown primitive IDs, and applicability outside `core`, `conditional`, or `supporting`. Assert valid order is preserved.

- [ ] **Step 2: Run focused tests and verify failure**

Run: `devbox run -- python -m unittest tests.test_generate_research_map.ResearchMapTests.test_validate_focus_use_cases_rejects_unknown_note`

Expected: FAIL because use-case loading/validation does not exist.

- [ ] **Step 3: Create the curated YAML**

Define exactly:

- `cf-hosted-coding-harnesses`
- `user-facing-agentic-applications`

Include all approved fields and evidence memberships from the design. Represent primitive applicability as a mapping from the three existing primitive IDs to `core`, `conditional`, or `supporting`.

- [ ] **Step 4: Implement loading and validation**

Add `FOCUS_USE_CASES_PATH`, `load_focus_use_cases()`, and `validate_focus_use_cases()`. Validate against note paths and validated primitive IDs without reordering configured lists.

- [ ] **Step 5: Verify and commit**

Run: `devbox run -- python -m unittest discover -s tests && devbox run validate`

Expected: PASS.

Run: `git add scripts/focus_use_cases.yaml scripts/generate_research_map.py tests/test_generate_research_map.py && git commit -m "feat: define workshop focus use cases"`

### Task 2: Reframe and render workshop outcome cards

**Files:**
- Modify: `scripts/generate_research_map.py`
- Modify: `tests/test_generate_research_map.py`

- [ ] **Step 1: Write failing content and order tests**

Assert the page says it summarizes workshop results rather than seeding a workshop; two use-case cards occur before three primitive cards and before tabs; use-case buttons have `aria-pressed="false"`; and each card contains outcome, POC, expandable lifecycle/authority/failure/capabilities/RFC/applicability/evidence content.

- [ ] **Step 2: Render the outcome hierarchy**

Render a workshop-results heading and summary, use-case section/cards, primitive section/cards, then tabbed matrices. Add a use-case **Show all** control separate from the primitive control.

- [ ] **Step 3: Style use-case cards**

Reuse typography and card language while visually distinguishing outcomes from primitives. Stack responsively above primitive cards and matrix tabs; avoid browser-default controls.

- [ ] **Step 4: Escape configuration content and preserve canonical links**

Escape all YAML-derived fields in static markup and any dynamic dialog templates. Render linked notes using existing canonical GitHub URLs.

- [ ] **Step 5: Verify and commit**

Run: `devbox run -- python -m unittest discover -s tests`

Expected: PASS.

Run: `git add scripts/generate_research_map.py tests/test_generate_research_map.py && git commit -m "feat: present workshop focus outcomes"`

### Task 3: Add independent use-case selection

**Files:**
- Modify: `scripts/generate_research_map.py`
- Modify: `tests/test_generate_research_map.py`

- [ ] **Step 1: Write failing state-contract tests**

Assert generated data contains use-case membership once and JavaScript defines `selectedUseCase`, `selectedPrimitive`, toggle/clear handlers for each layer, and one `noteMatchesSelection(noteId)` predicate.

- [ ] **Step 2: Embed use-case membership**

Build note-to-use-case relationship metadata (`core` or `supporting`) once, alongside primitive membership. Avoid duplicating complete note records.

- [ ] **Step 3: Implement independent card controls**

Use-case clicks toggle only `selectedUseCase`; primitive clicks continue to toggle only `selectedPrimitive`. Each Show-all control clears its own layer. Update `aria-pressed` independently.

- [ ] **Step 4: Implement matching semantics**

`noteMatchesSelection` returns use-case membership, primitive membership, their intersection, or true when neither is selected. Apply matching/dimmed classes without disabling markers.

- [ ] **Step 5: Verify and commit**

Run: `devbox run -- python -m unittest discover -s tests`

Expected: PASS.

Run: `git add scripts/generate_research_map.py tests/test_generate_research_map.py && git commit -m "feat: filter evidence by workshop use case"`

### Task 4: Update cluster counts, ordering, and empty state

**Files:**
- Modify: `scripts/generate_research_map.py`
- Modify: `tests/test_generate_research_map.py`

- [ ] **Step 1: Write failing intersection-cluster tests**

Use fixtures where a cluster has notes matching only the use case, only the primitive, both, and neither. Assert `matching/total` uses the current predicate, all notes remain in the picker, matching notes sort first stably, and clearing restores total counts/order.

- [ ] **Step 2: Reuse one matching predicate**

Replace primitive-only cluster logic with `noteMatchesSelection`. Update visible text and accessible labels consistently for use-case-only, primitive-only, and intersection states.

- [ ] **Step 3: Implement empty-intersection status**

Add a live or status region below filter cards. When both layers are selected and no note matches, show “No directly linked evidence for this use-case and primitive combination.” Clear it in other states or when matches exist.

- [ ] **Step 4: Update picker ordering and badges**

Sort a copy by current match status without mutating plot data. Show use-case and primitive core/supporting badges relevant to active selections. Preserve all entries and escaping.

- [ ] **Step 5: Verify and commit**

Run: `devbox run -- python -m unittest discover -s tests`

Expected: PASS.

Run: `git add scripts/generate_research_map.py tests/test_generate_research_map.py && git commit -m "feat: combine use-case and primitive evidence"`

### Task 5: Update details and protect accessibility regressions

**Files:**
- Modify: `scripts/generate_research_map.py`
- Modify: `tests/test_generate_research_map.py`

- [ ] **Step 1: Write failing detail-badge tests**

Assert individual dialogs show active use-case and primitive relationship badges when applicable, omit them otherwise, retain one close control and stable accessible name, and escape titles/summaries/tags/ratings/configuration text.

- [ ] **Step 2: Implement dialog membership badges**

Render selected use-case and primitive badges through escaped helper output. Keep core/supporting labels distinct and preserve canonical Markdown links.

- [ ] **Step 3: Protect existing keyboard and visual behavior**

Retain matrix Arrow/Home/End behavior, focus-visible restoration on dimmed markers, independent `aria-pressed` states, interactive unrelated markers, responsive card/tab classes, and backdrop/Escape dialog behavior.

- [ ] **Step 4: Run full regression suite**

Run: `devbox run -- python -m unittest discover -s tests`

Expected: PASS without Node or browser runtime dependencies.

- [ ] **Step 5: Commit interaction completion**

Run: `git add scripts/generate_research_map.py tests/test_generate_research_map.py && git commit -m "fix: preserve accessible workshop filtering"`

### Task 6: Regenerate and verify the workshop-results artifact

**Files:**
- Modify: `generated/research-map.html`

- [ ] **Step 1: Regenerate the page**

Run: `devbox run map`

Expected: generated HTML contains exactly two use-case cards above three primitive cards and six tabbed matrices.

- [ ] **Step 2: Run complete verification**

Run: `devbox run -- python -m unittest discover -s tests && devbox run validate && devbox run -- python scripts/summarize_ratings.py --check && devbox run -- python scripts/generate_research_map.py --check && git diff --check`

Expected: all commands exit 0.

- [ ] **Step 3: Inspect generated contracts**

Confirm workshop-result wording, card ordering, independent controls, intersection predicate, empty status, cluster count/accessibility updates, picker ordering, dialog badges, tab behavior, XSS escaping, and exactly two/three/six use-case/primitive/tab counts.

- [ ] **Step 4: Commit the artifact**

Run: `git add generated/research-map.html && git commit -m "chore: refresh workshop focus use cases"`

### Task 7: Final review and PR handoff

**Files:**
- Review: `scripts/focus_use_cases.yaml`
- Review: `scripts/platform_primitives.yaml`
- Review: `scripts/generate_research_map.py`
- Review: `tests/test_generate_research_map.py`
- Review: `generated/research-map.html`

- [ ] **Step 1: Run fresh verification**

Run: `devbox run -- python -m unittest discover -s tests && devbox run validate && devbox run -- python scripts/summarize_ratings.py --check && devbox run -- python scripts/generate_research_map.py --check && git diff --check`

Expected: all commands exit 0.

- [ ] **Step 2: Complete spec and quality reviews**

Review against `docs/superpowers/specs/2026-09-03-workshop-focus-use-cases-design.md`, then inspect configuration clarity, interaction correctness, accessibility, escaping, data size, and regressions. Fix every finding and re-review.

- [ ] **Step 3: Inspect branch scope**

Run: `git status --short --branch && git diff origin/feature/research-clustering-map...HEAD --stat`

Confirm only use-case configuration, generator/tests, generated artifact, and approved documentation are included. Leave unrelated Chromium, `.superpowers/`, and Nix files untouched.

- [ ] **Step 4: Request push confirmation**

Present results and verification evidence. Push to PR #42 only after explicit user approval.
