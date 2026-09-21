# Agentic Runtime Summit Deck

Ten-minute Cloud Foundry Summit working-group update: **from research to
sandboxing POCs**.

## Run locally

```bash
cd presentation
npm install
npm run slides
```

The Marp server prints a local preview URL. Export deliverables with:

```bash
cd presentation
npm run slides:pdf
npm run slides:html
```

PDF export needs a Chromium-compatible browser.

- **Linux:** Chromium is provided by Devbox. Nothing to install.
- **macOS:** Devbox excludes Chromium on Darwin, because the Nix package does
  not evaluate on Apple Silicon. Marp uses a locally installed Chrome, Edge, or
  Firefox instead — install one if you don't already have it, or point
  `CHROME_PATH` at an existing browser binary.

Generated files are written to `build/`, which is intentionally local output.

## Talk shape

The deck starts with repository and working-group momentum, explains the agent
loop at a conceptual level, and makes the local-tool execution boundary the
reason sandboxing is the first POC focus. The demo slide is deliberately a
placeholder until the POC leads select a scenario.

The activity figures are a repository snapshot from 20 September 2026:
63 PRs total, 43 merged, 20 open, and 3 open issues. OpenSandbox is described
as researched prior art linked to an open AAIF project proposal, not as an
adopted architecture.
