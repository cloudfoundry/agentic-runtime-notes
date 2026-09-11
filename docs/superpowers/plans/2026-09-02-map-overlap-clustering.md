# Map Overlap Clustering Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make exact-overlap notes render as count-bearing cluster markers with a picker overlay that keeps every note accessible.

**Architecture:** The Python generator will group each matrix's placed payload by exact `(x, y)` coordinates and emit either a singleton marker or a cluster marker carrying its note IDs. Browser JavaScript will use the marker's matrix and cluster data to render a picker, then reuse the existing detail rendering for the selected note. No scores are rounded or changed.

**Tech Stack:** Python 3.12, PyYAML, unittest, generated vanilla HTML/CSS/JavaScript.

---

## Files and Responsibilities

- Modify `scripts/generate_research_map.py`: grouping helper, cluster marker HTML, picker data, and picker/detail interaction behavior.
- Modify `tests/test_generate_research_map.py`: exact-overlap, singleton, per-matrix, count, picker, and single-close-button tests.
- Regenerate `generated/research-map.html`: checked-in artifact containing the clustering behavior.

### Task 1: Add testable overlap grouping

**Files:**
- Modify: `tests/test_generate_research_map.py`
- Modify: `scripts/generate_research_map.py`

- [ ] **Step 1: Write the failing grouping tests**

Add tests for a helper named `group_payload`:

```python
def test_group_payload_combines_only_exact_positions():
    payload = [
        {"id": "a", "position": {"x": 50, "y": 40}},
        {"id": "b", "position": {"x": 50, "y": 40}},
        {"id": "c", "position": {"x": 51, "y": 40}},
    ]
    groups = group_payload(payload)
    self.assertEqual([item["id"] for item in groups[(50, 40)]], ["a", "b"])
    self.assertEqual([item["id"] for item in groups[(51, 40)]], ["c"])

def test_group_payload_leaves_unplaced_items_out_of_coordinate_groups():
    self.assertEqual(group_payload([{"id": "a", "position": None}]), {})
```

- [ ] **Step 2: Run the focused tests and verify the expected failure**

Run: `devbox run -- python -m unittest tests.test_generate_research_map.ResearchMapTests.test_group_payload_combines_only_exact_positions`

Expected: FAIL with an import or attribute error because `group_payload` does not exist.

- [ ] **Step 3: Implement exact grouping**

Add `group_payload(payload)` that returns a dictionary keyed by `(position["x"], position["y"])`, skips items whose position is `None`, and preserves input order within each group. Do not round, bucket, jitter, or distance-cluster coordinates.

- [ ] **Step 4: Run grouping tests**

Run: `devbox run -- python -m unittest tests.test_generate_research_map.ResearchMapTests.test_group_payload_combines_only_exact_positions tests.test_generate_research_map.ResearchMapTests.test_group_payload_leaves_unplaced_items_out_of_coordinate_groups`

Expected: PASS.

- [ ] **Step 5: Commit the grouping behavior**

Run: `git add scripts/generate_research_map.py tests/test_generate_research_map.py && git commit -m "test: define exact map overlap grouping"`

### Task 2: Render singleton and cluster markers

**Files:**
- Modify: `scripts/generate_research_map.py`
- Modify: `tests/test_generate_research_map.py`

- [ ] **Step 1: Write failing HTML assertions**

Add a test using two notes with identical ratings and one with a nearby rating. Assert generated HTML contains a cluster marker with `data-cluster`, a visible count, and an individual marker for the nearby note. Assert the cluster label includes its count and that exact coordinate values remain unchanged in the marker style.

- [ ] **Step 2: Implement grouped marker generation**

Within each matrix, call `group_payload` and render one normal marker for a singleton group. Render one `<button class="marker cluster">` for a group of two or more, with `data-plot`, a stable encoded cluster key, `data-cluster`, visible count text, and an accessible label such as `2 notes at this position`. Add CSS that makes cluster markers visually distinct and readable.

- [ ] **Step 3: Add matrix isolation test**

Assert each matrix groups its own payload independently by checking that the generated HTML contains cluster metadata for a matrix only when its selected axis pair produces an exact overlap. Do not reuse cluster state between plot IDs.

- [ ] **Step 4: Run marker tests**

Run: `devbox run -- python -m unittest discover -s tests`

Expected: all existing tests and the new marker tests PASS.

- [ ] **Step 5: Commit marker rendering**

Run: `git add scripts/generate_research_map.py tests/test_generate_research_map.py && git commit -m "feat: render overlapping notes as clusters"`

### Task 3: Add the cluster picker and preserve one close control

**Files:**
- Modify: `scripts/generate_research_map.py`
- Modify: `tests/test_generate_research_map.py`

- [ ] **Step 1: Write failing picker assertions**

Assert generated HTML includes cluster note data, picker rendering code, note title and summary fields in the picker template, and exactly one static `class="close"` button. Assert the picker path invokes the same detail renderer rather than injecting a second close button.

- [ ] **Step 2: Implement picker data and behavior**

Embed cluster groups in the generated plot data or a cluster lookup keyed by plot ID and coordinate. On cluster click, render a picker inside the existing dialog containing one selectable item per note with type, title, and summary. Selecting an item calls the detail renderer and replaces picker contents. Keep the static dialog close button as the only close control; Escape continues to be handled by native dialog behavior, and clicking the backdrop closes it.

- [ ] **Step 3: Add accessible interaction attributes**

Use buttons for cluster markers and picker items, provide `aria-label` text for clusters, and ensure each picker item is keyboard reachable. Add a visible heading or introductory text identifying the number of notes in the cluster.

- [ ] **Step 4: Run interaction-oriented tests**

Run: `devbox run -- python -m unittest discover -s tests`

Expected: PASS with exactly one dialog close button in the generated markup.

- [ ] **Step 5: Commit picker behavior**

Run: `git add scripts/generate_research_map.py tests/test_generate_research_map.py && git commit -m "feat: add map overlap picker"`

### Task 4: Regenerate and verify the static artifact

**Files:**
- Modify: `generated/research-map.html`

- [ ] **Step 1: Regenerate the page**

Run: `devbox run map`

Expected: the generated HTML includes cluster markers where exact overlaps occur, cluster counts, picker code, and one dialog close button.

- [ ] **Step 2: Run complete verification**

Run: `devbox run -- python -m unittest discover -s tests && devbox run validate && devbox run -- python scripts/generate_research_map.py --check && git diff --check`

Expected: all tests PASS, all notes validate, the generated artifact is fresh, and no whitespace errors are reported.

- [ ] **Step 3: Inspect representative generated output**

Use a small script or browser inspection to confirm: cluster markers exist, nearby non-identical coordinates remain individual, picker note titles and summaries are embedded, and `class="close"` occurs exactly once.

- [ ] **Step 4: Commit the generated artifact**

Run: `git add generated/research-map.html && git commit -m "chore: refresh clustered research map"`

### Task 5: Final branch and PR verification

**Files:**
- Review: `scripts/generate_research_map.py`
- Review: `tests/test_generate_research_map.py`
- Review: `generated/research-map.html`

- [ ] **Step 1: Run the final verification commands**

Run: `devbox run -- python -m unittest discover -s tests && devbox run validate && devbox run -- python scripts/generate_research_map.py --check && git diff --check`

Expected: all commands exit 0.

- [ ] **Step 2: Review the diff**

Run: `git diff HEAD~4..HEAD --stat && git status --short --branch`

Confirm only clustering implementation, tests, and generated artifact changes are included; preserve unrelated untracked files.

- [ ] **Step 3: Push after explicit confirmation**

After the user confirms the grouped commit/push action, run `git push` so PR #42 receives the clustering commits. Do not post or resolve review comments unless separately requested.
