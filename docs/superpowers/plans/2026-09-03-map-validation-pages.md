# Map Validation and GitHub Pages Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fail CI when the checked-in research map differs from fresh generation and publish the verified HTML through GitHub Pages after relevant merges to `main`.

**Architecture:** The existing validation workflow will run the generator in write mode and use Git to prove the checked-in artifact remains unchanged. A separate main-only Pages workflow repeats repository validation, stages the verified artifact as `index.html`, uploads it with the official Pages artifact action, and deploys through the `github-pages` environment.

**Tech Stack:** GitHub Actions, Python 3.12, PyYAML, Git, official GitHub Pages actions.

---

## Files and Responsibilities

- Modify `.github/workflows/lint.yml`: regenerate the map and fail on a generated artifact diff.
- Create `.github/workflows/pages.yml`: validate and deploy the checked-in map on relevant `main` pushes.
- Create `tests/test_workflows.py`: parse workflow YAML and verify triggers, permissions, validation commands, Pages actions, and staging behavior.
- Update PR #42 description: add post-merge GitHub Pages setup reminder after explicit posting approval.

### Task 1: Test and extend generated-map validation

**Files:**
- Create: `tests/test_workflows.py`
- Modify: `.github/workflows/lint.yml`

- [ ] **Step 1: Write failing validation-workflow tests**

Load `.github/workflows/lint.yml` with `yaml.safe_load` and assert the validation job contains, in order:

```text
python .github/scripts/validate_notes.py
python scripts/summarize_ratings.py --check
python -m unittest discover -s tests
python scripts/generate_research_map.py
git diff --exit-code -- generated/research-map.html
```

Also assert pull-request and `main` push path filters cover `research/**`, `ideas/**`, `scripts/**`, `generated/**`, `tests/**`, and both relevant workflow files.

- [ ] **Step 2: Run the focused test and verify failure**

Run: `python -m unittest tests.test_workflows`

Expected: FAIL because validation currently runs generator `--check` instead of normal generation followed by Git diff.

- [ ] **Step 3: Update validation workflow**

Replace the current final map check with two explicit steps:

```yaml
- name: Generate research map
  run: python scripts/generate_research_map.py

- name: Verify generated map is checked in
  run: git diff --exit-code -- generated/research-map.html
```

Add `.github/workflows/pages.yml` to validation path filters so changes to deployment validation are tested.

- [ ] **Step 4: Run validation tests and repository checks**

Run: `python -m unittest tests.test_workflows && python -m unittest discover -s tests && python .github/scripts/validate_notes.py && python scripts/summarize_ratings.py --check`

Expected: PASS.

- [ ] **Step 5: Commit validation changes**

Run: `git add .github/workflows/lint.yml tests/test_workflows.py && git commit -m "ci: verify generated research map is committed"`

### Task 2: Prove stale-artifact detection

**Files:**
- Test: `generated/research-map.html`
- Test: one temporary generator input change that is restored after verification

- [ ] **Step 1: Verify a clean generation produces no diff**

Run: `python scripts/generate_research_map.py && git diff --exit-code -- generated/research-map.html`

Expected: PASS with no generated artifact diff.

- [ ] **Step 2: Create a temporary stale artifact**

Use `apply_patch` to add a harmless temporary comment to `generated/research-map.html`, then run:

`python scripts/generate_research_map.py && git diff --exit-code -- generated/research-map.html`

Expected: generation restores the canonical content, and Git diff exits non-zero because the committed artifact would differ from the temporary working-tree baseline only if the checked-in output is stale. To test stale source input instead, temporarily alter a copy or reversible generator text label, run generation and confirm Git diff fails.

- [ ] **Step 3: Restore only through canonical generation**

Undo the temporary generator-input change using `apply_patch`, then run `python scripts/generate_research_map.py`. Do not use destructive Git checkout/reset commands.

- [ ] **Step 4: Confirm clean state**

Run: `git diff --exit-code -- generated/research-map.html && git diff --check`

Expected: PASS.

### Task 3: Add the main-only GitHub Pages workflow

**Files:**
- Create: `.github/workflows/pages.yml`
- Modify: `tests/test_workflows.py`

- [ ] **Step 1: Write failing Pages workflow tests**

Assert `.github/workflows/pages.yml` has:

- Name `Deploy research map to Pages`.
- Push-only trigger for `main` and no pull-request trigger.
- Relevant path filters for notes, scripts/config, generated map, tests, and the Pages workflow.
- Permissions `contents: read`, `pages: write`, `id-token: write`.
- Concurrency group `pages` with `cancel-in-progress: true`.
- Validation, generation, and generated-file diff commands.
- `actions/configure-pages`, `actions/upload-pages-artifact`, and `actions/deploy-pages` official actions.
- A `github-pages` environment exposing `${{ steps.deployment.outputs.page_url }}`.

- [ ] **Step 2: Run focused tests and verify failure**

Run: `python -m unittest tests.test_workflows`

Expected: FAIL because `pages.yml` does not exist.

- [ ] **Step 3: Implement the Pages workflow**

Create a validation/build job that checks out, sets up Python 3.12, installs `pyyaml>=6`, runs the same validation sequence, creates `_site`, and copies `generated/research-map.html` to `_site/index.html`. Configure Pages and upload `_site`.

Create a deployment job depending on the build job, using `environment.name: github-pages`, `environment.url: ${{ steps.deployment.outputs.page_url }}`, and `actions/deploy-pages` with step ID `deployment`.

- [ ] **Step 4: Run workflow and repository tests**

Run: `python -m unittest discover -s tests && python .github/scripts/validate_notes.py && python scripts/summarize_ratings.py --check && python scripts/generate_research_map.py && git diff --exit-code -- generated/research-map.html && git diff --check`

Expected: PASS.

- [ ] **Step 5: Commit Pages workflow**

Run: `git add .github/workflows/pages.yml tests/test_workflows.py && git commit -m "ci: deploy research map to GitHub Pages"`

### Task 4: Final workflow review and verification

**Files:**
- Review: `.github/workflows/lint.yml`
- Review: `.github/workflows/pages.yml`
- Review: `tests/test_workflows.py`

- [ ] **Step 1: Validate workflow YAML and exact commands**

Run the workflow tests and inspect parsed values for YAML's `on` key behavior. Ensure tests account for PyYAML interpreting YAML 1.1 booleans if necessary without weakening assertions.

- [ ] **Step 2: Run the full local verification suite**

Run: `python -m unittest discover -s tests && python .github/scripts/validate_notes.py && python scripts/summarize_ratings.py --check && python scripts/generate_research_map.py && git diff --exit-code -- generated/research-map.html && git diff --check`

Expected: all commands exit 0.

- [ ] **Step 3: Review permissions and deployment boundaries**

Confirm the validation workflow has no write permissions, the Pages workflow grants only the three approved permissions, deploys only from `main`, and publishes only `_site/index.html` derived from the verified checked-in artifact.

- [ ] **Step 4: Inspect branch scope**

Run: `git status --short --branch && git diff origin/feature/research-clustering-map...HEAD --stat`

Confirm only workflow files, workflow tests, and approved documentation are included. Leave unrelated local Chromium, `.superpowers/`, Nix, and temporary files untouched.

### Task 5: Update PR description and handoff

**Files:**
- External: PR #42 description

- [ ] **Step 1: Prepare the PR reminder text**

Append:

```markdown
## Post-merge GitHub Pages setup

- [ ] Open repository **Settings -> Pages**.
- [ ] Under **Build and deployment**, select **GitHub Actions** as the source.
- [ ] Confirm **Deploy research map to Pages** succeeds on `main`.
- [ ] Verify the published Pages URL.
- [ ] Optionally add the URL to the repository description and README.
```

- [ ] **Step 2: Request grouped approval**

Present the final verification evidence and exact description update. Ask once for permission to push commits and update PR #42's description.

- [ ] **Step 3: Push and update only after approval**

Run `git push`, then use `gh pr edit 42 --body-file <prepared-file>` or equivalent while preserving the existing PR body and appending the reminder exactly once.

- [ ] **Step 4: Verify remote state**

Confirm PR #42 remains draft, points to `feature/research-clustering-map`, contains the setup reminder, and reports the expected validation check after push.
