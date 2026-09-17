# WebMCP Research Note Implementation Plan

> **For agentic workers:** Execute inline with validation checkpoints.

**Goal:** Add a sourced WebMCP research note and assess its Cloud Foundry relevance.

**Architecture:** Describe WebMCP as a browser-local tool exposure layer in which a page declares imperative JavaScript or declarative form tools, the browser mediates agent access, and the web application retains its current UI/session context.

**Tech Stack:** Markdown, YAML frontmatter, Devbox, Git, GitHub CLI.

---

### Task 1: Write `research/webmcp.md`

- [ ] Add valid frontmatter with WebMCP sources, tags `[inter-agent-comms, ecosystem-survey, governance]`, and `cf_areas: [capi, uaa]`.
- [ ] Explain WebMCP's motivation, browser-local tool model, imperative API, declarative form API, and fallback to ordinary browser automation.
- [ ] Cover shared browser state/authentication, tool descriptions/schemas, implementation status, and security-minded design.
- [ ] Assess CF relevance for applications exposing agent actions through existing browser sessions, while distinguishing WebMCP from server-side MCP gateways.
- [ ] Add questions about browser support, user consent, session identity, tool authorization, CSRF/security boundaries, and CF application guidance.

### Task 2: Validate and publish

- [ ] Run `devbox run validate`, `devbox run test`, and `git diff --check`.
- [ ] Stage only the note and approved spec/plan, commit `docs: add WebMCP research note`, push `research/webmcp`, and open a checklist-complete PR targeting `main`.
- [ ] Verify the PR metadata and CI status with `gh pr view`.
