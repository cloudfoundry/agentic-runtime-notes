# Map Validation and GitHub Pages Design

## Purpose

Guarantee that the checked-in research map is synchronized with its Markdown notes, ratings, plot configuration, platform primitives, focus use cases, and generator. Publish that reviewed artifact through GitHub Pages after changes merge to `main`.

## Validation workflow

Extend `.github/workflows/lint.yml` while retaining note validation, rating-distribution safeguards, and generator tests.

The map verification steps are:

1. Run `python scripts/generate_research_map.py`, which validates all generator inputs and writes `generated/research-map.html`.
2. Run `git diff --exit-code -- generated/research-map.html`.

Generator failures catch missing or invalid ratings, malformed primitive/use-case configuration, and unknown note references. The Git diff catches contributors changing any input without checking in the regenerated HTML.

The step name must clearly state the invariant, such as **Verify generated map is checked in**. Workflow path filters continue to cover `research/**`, `ideas/**`, `scripts/**`, `generated/**`, `tests/**`, and relevant workflow files.

## Pages workflow

Add `.github/workflows/pages.yml`, named **Deploy research map to Pages**.

It triggers only on relevant pushes to `main`; it has no pull-request trigger. Relevant paths include all map inputs, the generated artifact, tests, and the Pages workflow itself.

Use these minimal permissions:

- `contents: read`
- `pages: write`
- `id-token: write`

Use a `pages` concurrency group and cancel an in-progress older deployment when a newer relevant `main` push arrives.

## Build and deployment

The Pages workflow checks out the repository, configures Python 3.12, installs PyYAML, and runs:

1. Note validation.
2. Rating-distribution safeguards.
3. Generator tests.
4. Normal map generation.
5. `git diff --exit-code -- generated/research-map.html`.

After successful validation, create a staging directory containing the verified file as `index.html`. Upload that directory with the official Pages artifact action and deploy it with the official Pages deployment action through the `github-pages` environment. Expose the deployment URL through the environment metadata.

The deployment publishes the checked-in artifact after proving it is byte-for-byte identical to fresh generation. It must not publish a different, unreviewed generated result.

## Repository setup reminder

The current repository does not yet have GitHub Pages configured. Add this reminder to PR #42's description:

1. After merging, open repository **Settings -> Pages**.
2. Under **Build and deployment**, select **GitHub Actions** as the source.
3. Confirm **Deploy research map to Pages** succeeds on `main`.
4. Verify the published Pages URL.
5. Optionally add the published URL to the repository description and README in a follow-up.

The workflow is added in this PR and remains dormant until a relevant push reaches `main`.

## Verification

Tests or workflow-oriented checks must verify trigger branches and paths, minimal permissions, concurrency, validation commands, normal generation followed by generated-file diff checking, artifact staging as `index.html`, official Pages actions, and the `github-pages` environment.

Run the complete local test and validation suite and simulate the stale-artifact failure by changing a generator input or generated artifact, confirming the diff step fails, then regenerating and confirming it passes.
