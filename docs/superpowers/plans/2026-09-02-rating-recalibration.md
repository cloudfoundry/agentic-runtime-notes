# Rating Recalibration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace heuristic ratings on every research note and idea with full-document, evidence-based scores that use fixed semantic rubrics and corpus-wide comparative calibration.

**Architecture:** Each document remains the source of truth for four rating objects and evidence-specific notes. Review documents independently in manageable batches without consulting their existing values, then analyze the complete corpus for inconsistent judgments and severe distribution collapse. Regenerate the static map only after calibrated source ratings pass coverage and distribution safeguards.

**Tech Stack:** Markdown/YAML frontmatter, Python 3.12, PyYAML, unittest, generated HTML.

---

## Files and Responsibilities

- Modify every non-template `research/*.md`: recalibrated `platform-impact`, `maturity`, `novelty`, and `actionability` values and notes.
- Modify every non-template `ideas/*.md`: the same recalibrated rating objects.
- Modify `tests/test_generate_research_map.py`: conservative safeguards against severe range collapse and missing evidence notes.
- Create `scripts/summarize_ratings.py`: deterministic corpus summary for range, quartile, distinct-value, correlation, and quadrant review.
- Modify `.github/workflows/lint.yml`: run the rating summary's validation mode if appropriate.
- Regenerate `generated/research-map.html`: calibrated map artifact.

### Task 1: Add corpus diagnostics and conservative safeguards

**Files:**
- Create: `scripts/summarize_ratings.py`
- Modify: `tests/test_generate_research_map.py`

- [ ] **Step 1: Write failing safeguard tests**

Add tests for a pure `summarize_ratings(notes)` function. Use fixtures proving it returns `count`, `minimum`, `maximum`, `distinct`, `median`, first/third quartiles, and quadrant counts. Add a validation test that rejects a synthetic corpus where an entire required rating lies strictly above 50 or has fewer than five distinct values.

- [ ] **Step 2: Run tests and verify the expected failure**

Run: `devbox run -- python -m unittest tests.test_generate_research_map`

Expected: FAIL because `scripts.summarize_ratings` does not exist.

- [ ] **Step 3: Implement the diagnostic script**

Implement `summarize_ratings(notes)` using Python standard-library statistics. The CLI loads notes through `scripts.generate_research_map.load_notes`, prints per-rating count/min/max/median/quartiles/distinct values, Pearson correlations, and six matrix quadrant counts. Add `--check` that fails only when a required rating is missing, a rating has fewer than five distinct values, or every value lies strictly on one side of 50. These are severe-collapse guards, not distribution targets.

- [ ] **Step 4: Verify diagnostics against synthetic fixtures**

Run: `devbox run -- python -m unittest tests.test_generate_research_map`

Expected: tests PASS, while `devbox run -- python scripts/summarize_ratings.py --check` still fails against the current coarse corpus.

- [ ] **Step 5: Commit diagnostics**

Run: `git add scripts/summarize_ratings.py tests/test_generate_research_map.py && git commit -m "test: add rating distribution safeguards"`

### Task 2: Independently re-evaluate research notes, batch 1

**Files:**
- Modify: `research/a2a-protocol.md` through `research/hatchet.md`, alphabetically, excluding templates/readmes.

- [ ] **Step 1: Read each complete document**

For each file, read frontmatter and all body sections. Do not use the current values as anchors. Record evidence for current CF gap, technology maturity, technical novelty, and clarity of a concrete CF next step.

- [ ] **Step 2: Replace all four rating objects**

Assign integer values using the rubric anchors in `docs/superpowers/specs/2026-09-02-rating-recalibration-design.md`. Rewrite every `note` with document-specific evidence. Avoid generic phrases such as “this score reflects”.

- [ ] **Step 3: Review within-batch consistency**

Compare similar technologies in the batch. Confirm a higher score has a rubric-based reason and that scores are not mechanically tied to tags or note type.

- [ ] **Step 4: Validate the batch**

Run: `devbox run validate && devbox run -- python -m unittest discover -s tests`

Expected: note schema and tests PASS.

- [ ] **Step 5: Commit batch 1**

Run: `git add research && git commit -m "docs: recalibrate research ratings batch one"`

### Task 3: Independently re-evaluate research notes, batch 2

**Files:**
- Modify: remaining non-template `research/*.md` files alphabetically after `hatchet.md`.

- [ ] **Step 1: Read each complete document without consulting old values**

Evaluate the same four evidence categories against fixed rubric anchors.

- [ ] **Step 2: Replace values and generic notes**

Write four evidence-specific rating objects per file. Platform impact means current CF gap, not ecosystem importance or potential impact.

- [ ] **Step 3: Compare related technologies**

Check relative consistency among frameworks, protocols, managed runtimes, execution systems, isolation technologies, and observability standards while preserving their absolute rubric meaning.

- [ ] **Step 4: Validate the batch**

Run: `devbox run validate && devbox run -- python -m unittest discover -s tests`

Expected: PASS.

- [ ] **Step 5: Commit batch 2**

Run: `git add research && git commit -m "docs: recalibrate research ratings batch two"`

### Task 4: Independently re-evaluate all ideas

**Files:**
- Modify: every non-template `ideas/*.md`.

- [ ] **Step 1: Read each complete idea**

Use the idea's rationale, related work, and proposed next research to score the current CF gap, maturity of its underlying technical approach, technical novelty, and next-step clarity.

- [ ] **Step 2: Replace all rating values and notes**

Do not automatically rate ideas as less mature or more novel than research notes. Score the underlying capability or architecture; use the document's concreteness specifically for actionability.

- [ ] **Step 3: Review idea/research consistency**

Compare ideas with their linked research notes. Explain legitimate differences through the rating notes rather than forcing equal values.

- [ ] **Step 4: Validate and commit**

Run: `devbox run validate && devbox run -- python -m unittest discover -s tests`

Expected: PASS.

Run: `git add ideas && git commit -m "docs: recalibrate idea ratings"`

### Task 5: Perform corpus-wide hybrid calibration

**Files:**
- Modify: any rated note whose comparison reveals a rubric inconsistency.

- [ ] **Step 1: Generate the corpus summary**

Run: `devbox run -- python scripts/summarize_ratings.py`

Review per-rating ranges, quartiles, distinct-value counts, correlations, and six matrix quadrant counts.

- [ ] **Step 2: Compare scoring outliers and near-neighbors**

For each attribute, inspect documents at the minimum, maximum, quartile boundaries, and duplicate-heavy values. Confirm their order against the semantic rubric and document evidence.

- [ ] **Step 3: Correct only inconsistent judgments**

Adjust scores or notes where full-document evidence does not support the current relative order or absolute anchor. Do not percentile-stretch values and do not assign quadrant quotas.

- [ ] **Step 4: Run severe-collapse safeguards**

Run: `devbox run -- python scripts/summarize_ratings.py --check`

Expected: PASS with all four ratings represented by at least five distinct values and values occurring on both sides of 50.

- [ ] **Step 5: Commit calibration corrections**

Run: `git add research ideas && git commit -m "docs: calibrate ratings across the corpus"`

### Task 6: Integrate diagnostics into CI and regenerate the map

**Files:**
- Modify: `.github/workflows/lint.yml`
- Modify: `generated/research-map.html`

- [ ] **Step 1: Add the safeguard command to CI**

Add `python scripts/summarize_ratings.py --check` after note validation and before generated-map freshness validation. Include `scripts/summarize_ratings.py` in workflow path filters through the existing `scripts/**` rule.

- [ ] **Step 2: Regenerate the map**

Run: `devbox run map`

Expected: the six matrices reflect recalibrated source values and existing cluster/list interaction behavior remains intact.

- [ ] **Step 3: Run complete verification**

Run: `devbox run -- python -m unittest discover -s tests && devbox run validate && devbox run -- python scripts/summarize_ratings.py --check && devbox run -- python scripts/generate_research_map.py --check && git diff --check`

Expected: all commands exit 0.

- [ ] **Step 4: Review the final summary**

Run `devbox run -- python scripts/summarize_ratings.py` and save the key ranges, quartiles, correlations, and quadrant counts for the PR summary. Verify the distribution is plausible rather than merely broad.

- [ ] **Step 5: Commit CI and artifact updates**

Run: `git add .github/workflows/lint.yml generated/research-map.html && git commit -m "ci: validate recalibrated ratings"`

### Task 7: Final review and PR handoff

**Files:**
- Review: all changed `research/*.md` and `ideas/*.md`
- Review: `scripts/summarize_ratings.py`
- Review: `generated/research-map.html`

- [ ] **Step 1: Verify full coverage and no generic notes**

Use a script to confirm all 41 tracked notes, plus any in-scope untracked contribution, have four values and non-empty notes. Search for the old generic wording `Initial review of` and `this score reflects`; expected result is no matches in rating notes.

- [ ] **Step 2: Run final verification afresh**

Run: `devbox run -- python -m unittest discover -s tests && devbox run validate && devbox run -- python scripts/summarize_ratings.py --check && devbox run -- python scripts/generate_research_map.py --check && git diff --check`

Expected: all commands exit 0.

- [ ] **Step 3: Review branch scope**

Run: `git status --short --branch && git diff origin/feature/research-clustering-map...HEAD --stat`

Confirm unrelated Nix directories and `.superpowers/` remain excluded. Handle `research/domyn-swarm.md` according to whether it is tracked or intentionally part of this PR at execution time; never stage it accidentally.

- [ ] **Step 4: Request commit/push confirmation**

Present the recalibration summary and ask for explicit permission before pushing commits to PR #42.
