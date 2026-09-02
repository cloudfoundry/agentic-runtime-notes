# Platform Primitives Workshop View Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Present three strategic platform primitives above tabbed rating matrices and persistently highlight their related research and ideas.

**Architecture:** A curated YAML file defines primitive content and core/supporting note paths. The Python generator validates and embeds this data, renders cards and accessible matrix tabs, and annotates markers with note membership. Browser-side JavaScript manages primitive selection, marker dimming, mixed-cluster counts, related-first picker ordering, and tab keyboard behavior in the static page.

**Tech Stack:** Python 3.12, PyYAML, unittest, generated vanilla HTML/CSS/JavaScript.

---

## Files and Responsibilities

- Create `scripts/platform_primitives.yaml`: strategic primitive descriptions and ordered core/supporting note memberships.
- Modify `scripts/generate_research_map.py`: primitive loading/validation, cards, tabs, membership metadata, highlighting, and mixed-cluster interaction.
- Modify `tests/test_generate_research_map.py`: configuration validation and generated interaction/accessibility tests.
- Modify `generated/research-map.html`: regenerated static workshop artifact.

### Task 1: Define and validate platform primitive content

**Files:**
- Create: `scripts/platform_primitives.yaml`
- Modify: `scripts/generate_research_map.py`
- Modify: `tests/test_generate_research_map.py`

- [ ] **Step 1: Write failing primitive validation tests**

Add tests for `validate_primitives(primitives, known_paths)` covering required fields, duplicate IDs, empty core membership, duplicate membership within one primitive, and unknown note paths. Add a valid fixture asserting core/supporting order is preserved.

- [ ] **Step 2: Run focused tests and verify failure**

Run: `devbox run -- python -m unittest tests.test_generate_research_map.ResearchMapTests.test_validate_primitives_rejects_unknown_note`

Expected: FAIL because primitive loading and validation do not exist.

- [ ] **Step 3: Add the curated YAML**

Define these IDs and content from the approved design:

- `durable-addressable-execution`
- `attested-workload-authority`
- `session-scoped-isolated-execution`

Each entry includes `title`, `proposition`, `cf_gap`, `strategic_decision`, `poc`, `rfc_scope`, `core`, and `supporting`. Use repository-relative Markdown paths and the note memberships established during the three independent cluster analyses.

- [ ] **Step 4: Implement loading and validation**

Add `PRIMITIVES_PATH`, `load_primitives()`, and `validate_primitives()`. Reject non-list configuration, missing/blank string fields, duplicate IDs, empty core lists, paths repeated across core/supporting in one primitive, and paths absent from `load_notes()`. Return validated entries without reordering memberships.

- [ ] **Step 5: Run tests and commit**

Run: `devbox run -- python -m unittest discover -s tests && devbox run validate`

Expected: PASS.

Run: `git add scripts/platform_primitives.yaml scripts/generate_research_map.py tests/test_generate_research_map.py && git commit -m "feat: define strategic platform primitives"`

### Task 2: Render primitive cards and accessible matrix tabs

**Files:**
- Modify: `scripts/generate_research_map.py`
- Modify: `tests/test_generate_research_map.py`

- [ ] **Step 1: Write failing card and tab markup tests**

Assert generated HTML contains three primitive card buttons with `aria-pressed="false"`, a **Show all** control, proposition/decision content, expandable gap/POC/RFC details, a `role="tablist"`, six `role="tab"` controls, matching `role="tabpanel"` sections, one initially active tab, and hidden inactive panels.

- [ ] **Step 2: Implement primitive card markup**

Render cards above matrices. Each card button carries `data-primitive`, `aria-pressed`, and a stable accent custom property. Keep longer content in an expandable details area and render core/supporting note links using canonical GitHub URLs.

- [ ] **Step 3: Convert matrices to tabs**

Render a tab strip and panel per plot. Connect `aria-controls`, `aria-labelledby`, tab IDs, panel IDs, `aria-selected`, and `hidden`. Keep all matrix marker data in the document so filtering does not require regeneration.

- [ ] **Step 4: Add responsive visual styles**

Style cards, selected states, details, tab controls, active/inactive panels, and mobile stacking/scrolling using the page's existing typography and dark palette. Avoid browser-default grey controls.

- [ ] **Step 5: Verify and commit**

Run: `devbox run -- python -m unittest discover -s tests`

Expected: PASS.

Run: `git add scripts/generate_research_map.py tests/test_generate_research_map.py && git commit -m "feat: add primitive cards and matrix tabs"`

### Task 3: Add persistent primitive highlighting

**Files:**
- Modify: `scripts/generate_research_map.py`
- Modify: `tests/test_generate_research_map.py`

- [ ] **Step 1: Write failing highlight behavior assertions**

Assert generated data includes primitive membership per note, cards expose stable IDs, and JavaScript contains explicit selection, clear, and matrix-refresh functions. Assert related markers receive a related state while unrelated markers receive a dimmed state without becoming disabled.

- [ ] **Step 2: Embed membership data**

Build a mapping from note path to primitive IDs and relationship type (`core` or `supporting`). Include it once in embedded page data and annotate single markers with their note path; do not duplicate full note data beyond existing plot payloads.

- [ ] **Step 3: Implement persistent selection**

Track `selectedPrimitive`. Card clicks select or toggle it, **Show all** clears it, and `aria-pressed` updates. Apply CSS classes/custom properties to related and unrelated markers in all panels so state persists when tabs change. Unrelated markers remain clickable and keyboard accessible.

- [ ] **Step 4: Show primitive membership in note detail**

When a selected primitive contains the opened note, render a core/supporting badge in the existing detail dialog.

- [ ] **Step 5: Verify and commit**

Run: `devbox run -- python -m unittest discover -s tests`

Expected: PASS.

Run: `git add scripts/generate_research_map.py tests/test_generate_research_map.py && git commit -m "feat: highlight notes by platform primitive"`

### Task 4: Handle mixed clusters under highlighting

**Files:**
- Modify: `scripts/generate_research_map.py`
- Modify: `tests/test_generate_research_map.py`

- [ ] **Step 1: Write failing mixed-cluster tests**

Create a fixture cluster with two related and three unrelated notes. Assert the default marker count is `5`, selected-state text becomes `2/5`, the cluster remains interactive, and picker ordering places the two related notes first while retaining all five.

- [ ] **Step 2: Embed cluster note IDs**

Ensure each cluster marker can resolve its complete ordered note list without coordinate string parsing ambiguity. Keep clustering independent per matrix.

- [ ] **Step 3: Implement selected cluster display**

On primitive selection, compute related members for each cluster. Use the primitive accent and `related/total` text when at least one member is related; dim the cluster only when no member is related. Restore total count after clearing.

- [ ] **Step 4: Sort and label the picker**

Sort a cluster picker copy by selected-primitive membership while preserving original order within related/unrelated groups. Add core/supporting badges to related entries. Do not mutate embedded plot arrays.

- [ ] **Step 5: Verify and commit**

Run: `devbox run -- python -m unittest discover -s tests`

Expected: PASS.

Run: `git add scripts/generate_research_map.py tests/test_generate_research_map.py && git commit -m "feat: filter mixed map clusters"`

### Task 5: Add keyboard tab behavior and interaction regression coverage

**Files:**
- Modify: `scripts/generate_research_map.py`
- Modify: `tests/test_generate_research_map.py`

- [ ] **Step 1: Write failing tab-keyboard assertions**

Assert JavaScript handles ArrowLeft, ArrowRight, Home, and End on the tablist, wraps arrow navigation, updates `aria-selected`/`tabIndex`, hides inactive panels, and moves focus to the activated tab.

- [ ] **Step 2: Implement tab activation**

Add one `activateTab(index)` function used by both click and keyboard handlers. Preserve `selectedPrimitive` and rerun marker highlighting after activation.

- [ ] **Step 3: Protect existing interactions**

Retain tests for singleton marker clicks, cluster picker selection, close button, backdrop/Escape behavior, note-type badges, canonical GitHub links, one close control, and generated JavaScript syntax.

- [ ] **Step 4: Run all tests**

Run: `devbox run -- python -m unittest discover -s tests`

Expected: PASS.

- [ ] **Step 5: Commit interaction completion**

Run: `git add scripts/generate_research_map.py tests/test_generate_research_map.py && git commit -m "feat: add accessible matrix navigation"`

### Task 6: Regenerate and verify the workshop artifact

**Files:**
- Modify: `generated/research-map.html`

- [ ] **Step 1: Regenerate the static page**

Run: `devbox run map`

Expected: the page contains three primitive cards, six tabbed matrices, primitive content, membership data, and highlighting behavior.

- [ ] **Step 2: Run complete repository verification**

Run: `devbox run -- python -m unittest discover -s tests && devbox run validate && devbox run -- python scripts/summarize_ratings.py --check && devbox run -- python scripts/generate_research_map.py --check && git diff --check`

Expected: all commands exit 0.

- [ ] **Step 3: Inspect generated behavior**

Confirm generated JavaScript parses; exactly three primitive cards and six tabs/panels exist; selecting a primitive dims unrelated markers; clearing restores all markers; a mixed cluster displays related/total; its picker lists related notes first; and keyboard tabs update panel visibility.

- [ ] **Step 4: Commit generated output**

Run: `git add generated/research-map.html && git commit -m "chore: refresh platform primitives workshop view"`

### Task 7: Final review and PR handoff

**Files:**
- Review: `scripts/platform_primitives.yaml`
- Review: `scripts/generate_research_map.py`
- Review: `tests/test_generate_research_map.py`
- Review: `generated/research-map.html`

- [ ] **Step 1: Run final verification afresh**

Run: `devbox run -- python -m unittest discover -s tests && devbox run validate && devbox run -- python scripts/summarize_ratings.py --check && devbox run -- python scripts/generate_research_map.py --check && git diff --check`

Expected: all commands exit 0.

- [ ] **Step 2: Perform spec and quality reviews**

Review all requirements in `docs/superpowers/specs/2026-09-02-platform-primitives-workshop-view-design.md`, then inspect generated accessibility, static data size, configuration clarity, and interaction regressions. Fix and re-review every finding before handoff.

- [ ] **Step 3: Inspect branch scope**

Run: `git status --short --branch && git diff origin/feature/research-clustering-map...HEAD --stat`

Confirm unrelated `.superpowers/` and Nix directories remain excluded.

- [ ] **Step 4: Request push confirmation**

Present the workshop-view summary and verification evidence. Push to PR #42 only after explicit user confirmation.
