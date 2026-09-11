# Research Clustering Map Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate a responsive static HTML quadrant map from the repository's ideas and research notes, with reusable frontmatter ratings, per-rating justifications, and clickable GitHub-linked detail overlays.

**Architecture:** A Python generator will parse Markdown frontmatter and summaries, validate rating objects, derive plot coordinates from named ratings, and emit a self-contained HTML document. Plot definitions remain separate from note data so future plots can select different rating names. Existing notes receive a manual initial rating pass; the generator never infers or overwrites ratings.

**Tech Stack:** Python 3.12, PyYAML, unittest or pytest-compatible tests, vanilla HTML/CSS/JavaScript.

---

## Files and Responsibilities

- Create `scripts/generate_research_map.py`: frontmatter parsing, summary extraction, rating validation, plot configuration, GitHub URL generation, and HTML generation.
- Create `scripts/research_map_plots.yaml`: named plot definitions, initially `platform-impact-maturity`.
- Create `tests/test_generate_research_map.py`: unit tests for parsing, validation, coordinate derivation, summaries, and URLs.
- Create `generated/research-map.html`: generated static artifact for local or GitHub Pages hosting.
- Modify every non-template file in `research/` and `ideas/`: add the four manually reviewed rating objects and justifications.
- Modify `research/TEMPLATE.md` and `ideas/TEMPLATE.md`: document the optional rating schema and example.
- Modify `research/README.md` and `ideas/README.md`: document rating meaning, 0-100 scale, and the map-generation command.
- Modify `devbox.json`: add a `map` script that runs the generator.
- Modify `.github/workflows/lint.yml` or the applicable workflow: run map generation/validation and tests if CI currently owns repository checks.

### Task 1: Define the rating contract and test fixtures

**Files:**
- Modify: `research/TEMPLATE.md`
- Modify: `ideas/TEMPLATE.md`
- Modify: `research/README.md`
- Modify: `ideas/README.md`
- Create: `tests/test_generate_research_map.py`

- [ ] **Step 1: Add the frontmatter example and field documentation**

Document this exact shape in both templates/readmes:

```yaml
ratings:
  platform-impact:
    value: 80
    note: "Touches core runtime and governance concerns across many deployments."
  maturity:
    value: 55
    note: "Strong external prior art, but patterns are still evolving."
  novelty:
    value: 70
    note: "Combines established capabilities in a comparatively new runtime context."
  actionability:
    value: 45
    note: "Needs further comparison before a focused POC can be selected."
```

State that values are provisional working-group judgments, must be integers from 0 through 100, and each value requires a non-empty note.

- [ ] **Step 2: Write failing parser and rating tests**

Add fixtures and tests for:

```python
def test_parse_note_extracts_metadata_and_research_summary():
    note = parse_note(Path("research/example.md"), text)
    assert note.title == "Example"
    assert note.kind == "research"
    assert note.summary == "A concise summary."

def test_validate_ratings_rejects_out_of_range_value():
    with pytest.raises(ValueError, match="0..100"):
        validate_ratings({"maturity": {"value": 101, "note": "reason"}})

def test_validate_ratings_requires_note():
    with pytest.raises(ValueError, match="non-empty note"):
        validate_ratings({"maturity": {"value": 50, "note": ""}})
```

Use temporary Markdown text in tests so parser behavior is isolated from current note contents.

- [ ] **Step 3: Run the focused tests and verify they fail**

Run: `python -m pytest tests/test_generate_research_map.py -q`

Expected: FAIL because the generator module and parsing/validation functions do not yet exist.

- [ ] **Step 4: Commit the contract and failing tests**

Run: `git add research/TEMPLATE.md ideas/TEMPLATE.md research/README.md ideas/README.md tests/test_generate_research_map.py && git commit -m "test: define research map rating contract"`

### Task 2: Implement parsing, validation, and plot coordinates

**Files:**
- Create: `scripts/generate_research_map.py`
- Create: `scripts/research_map_plots.yaml`
- Modify: `tests/test_generate_research_map.py`

- [ ] **Step 1: Add the initial plot configuration**

Create `scripts/research_map_plots.yaml` with:

```yaml
platform-impact-maturity:
  title: Platform Impact x Maturity
  x:
    rating: maturity
    label: Maturity
    low: Emerging
    high: Established
  y:
    rating: platform-impact
    label: Platform Impact
    low: Local concern
    high: Platform-wide concern
```

- [ ] **Step 2: Implement the smallest passing parser and validator**

Implement typed note data and functions named `parse_frontmatter`, `extract_summary`, `validate_ratings`, `load_note`, and `derive_position`. Parse YAML between leading `---` delimiters, select `Summary` for research and `The idea` for ideas, strip Markdown formatting only as needed for a short plain-text preview, and use the first substantive paragraph as fallback. Reject malformed YAML, non-mapping rating entries, missing `value`/`note`, non-integer values, values outside `0..100`, and blank notes. `derive_position` must return `None` when either configured rating is absent and otherwise return the selected values as x/y percentages.

- [ ] **Step 3: Add tests for plot derivation, fallback summaries, URLs, and malformed input**

Add tests equivalent to:

```python
def test_derive_position_maps_x_and_y_from_named_ratings():
    ratings = {
        "maturity": {"value": 55, "note": "reason"},
        "platform-impact": {"value": 80, "note": "reason"},
    }
    assert derive_position(ratings, plots["platform-impact-maturity"]) == {"x": 55, "y": 80}

def test_missing_plot_rating_is_unplaced():
    assert derive_position({"maturity": {"value": 55, "note": "reason"}}, plot) is None

def test_github_url_uses_canonical_repository_path():
    assert github_url(Path("research/langgraph.md")) == "https://github.com/cloudfoundry/agentic-runtime-notes/blob/main/research/langgraph.md"
```

- [ ] **Step 4: Run focused tests and repository validation**

Run: `python -m pytest tests/test_generate_research_map.py -q && python .github/scripts/validate_notes.py`

Expected: new focused tests PASS; existing note validation remains PASS before ratings are added because ratings are optional during this task.

- [ ] **Step 5: Commit the generator core**

Run: `git add scripts/research_map_plots.yaml scripts/generate_research_map.py tests/test_generate_research_map.py && git commit -m "feat: add research map data model"`

### Task 3: Manually rate every existing note

**Files:**
- Modify: every `research/*.md` except `README.md` and `TEMPLATE.md`
- Modify: every `ideas/*.md` except `README.md` and `TEMPLATE.md`

- [ ] **Step 1: Build the complete note inventory**

Run: `python -c 'from pathlib import Path; print("\\n".join(str(p) for d in (Path("research"), Path("ideas")) for p in sorted(d.glob("*.md")) if p.name not in {"README.md", "TEMPLATE.md"}))'`

Use each note's title, tags, summary/idea, findings, and open questions to make a deliberate judgment. Do not assign scores from filename order or silently omit a note.

- [ ] **Step 2: Add four rating objects to each note**

Add `platform-impact`, `maturity`, `novelty`, and `actionability` objects using integer values `0..100` and concise note-specific justifications. Keep existing frontmatter and body content unchanged apart from this addition.

- [ ] **Step 3: Add a coverage test**

Add a test that loads every current note and asserts all four rating names exist, every value is an integer in range, and every note is non-empty. This makes the initial rating pass explicit and prevents accidental omissions.

- [ ] **Step 4: Run coverage and note validation**

Run: `python -m pytest tests/test_generate_research_map.py -q && python .github/scripts/validate_notes.py`

Expected: all rating coverage tests and existing repository validation PASS.

- [ ] **Step 5: Commit the manual rating pass**

Run: `git add research ideas tests/test_generate_research_map.py && git commit -m "feat: add initial research map ratings"`

### Task 4: Generate the interactive static page

**Files:**
- Modify: `scripts/generate_research_map.py`
- Create: `generated/research-map.html`
- Modify: `tests/test_generate_research_map.py`

- [ ] **Step 1: Write failing output and interaction assertions**

Test generated HTML for the configured plot title, axis labels, note titles, distinct idea/research marker classes, canonical GitHub URLs, embedded rating notes, an accessible dialog/overlay, Escape handling, and an unplaced-note list.

- [ ] **Step 2: Implement deterministic HTML generation**

Generate a self-contained document with embedded JSON note data. Render x/y as percentages from the selected rating values, add a legend and provisional-rating notice, make markers buttons with accessible labels, and show a dialog containing summary, tags, author/date, all four ratings and notes, and the GitHub link. Render notes missing either selected rating in an unplaced list. Escape must close the dialog; clicking outside may also close it. Keep CSS responsive with a taller map canvas at narrow widths.

- [ ] **Step 3: Generate and inspect the artifact**

Run: `python scripts/generate_research_map.py`

Expected: `generated/research-map.html` is created and contains all current notes, with no external runtime dependency.

- [ ] **Step 4: Run all tests**

Run: `python -m pytest -q`

Expected: PASS.

- [ ] **Step 5: Commit the page and renderer**

Run: `git add scripts/generate_research_map.py generated/research-map.html tests/test_generate_research_map.py && git commit -m "feat: generate interactive research map"`

### Task 5: Wire commands and CI validation

**Files:**
- Modify: `devbox.json`
- Modify: `.github/workflows/lint.yml`
- Modify: `scripts/generate_research_map.py`

- [ ] **Step 1: Add the repository command**

Add a Devbox script named `map` running `python scripts/generate_research_map.py`. The generator should support a `--check` option that regenerates in memory and exits non-zero if the checked-in HTML differs from the expected output.

- [ ] **Step 2: Add CI checks**

Extend the existing lint workflow to run the generator check, the note validator, and the test suite using the repository's existing Python/Devbox setup. Do not add a second workflow if the current one can own these checks.

- [ ] **Step 3: Test normal and stale-artifact behavior**

Run: `devbox run map && devbox run validate && python -m pytest -q`

Then make a temporary change to the generated artifact, run `python scripts/generate_research_map.py --check`, and verify it fails; regenerate and verify it passes. Restore only the generated artifact through the generator, not with a destructive Git command.

- [ ] **Step 4: Commit command and CI integration**

Run: `git add devbox.json .github/workflows/lint.yml scripts/generate_research_map.py generated/research-map.html && git commit -m "ci: validate generated research map"`

### Task 6: Final review of the workshop artifact

**Files:**
- Review: `generated/research-map.html`
- Review: all rated notes and `scripts/research_map_plots.yaml`

- [ ] **Step 1: Verify complete data coverage**

Run: `python -m pytest -q && python .github/scripts/validate_notes.py && python scripts/generate_research_map.py --check`

Expected: all commands PASS.

- [ ] **Step 2: Check the page in a browser**

Open `generated/research-map.html` through a static server, click representative idea and research markers, verify overlay contents and GitHub links, close with Escape, and inspect the narrow-screen layout.

- [ ] **Step 3: Review score justifications**

Confirm every note has four note-specific explanations, no rating is presented as objective fact, and the page clearly labels the scores as initial/provisional working-group judgments.

- [ ] **Step 4: Commit any final generated artifact update**

Run: `git status --short && git diff --check && git add generated/research-map.html && git commit -m "chore: refresh research map"` only if the generated artifact changed after the final review.
