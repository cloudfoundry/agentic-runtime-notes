# MCP Apps Research Note Implementation Plan

> **For agentic workers:** Execute inline with validation checkpoints.

**Goal:** Add a sourced MCP Apps research note and assess its Cloud Foundry relevance.

**Architecture:** Describe MCP Apps as a server-declared UI resource model: tools associate `ui://` HTML resources, hosts render them in sandboxed iframes, and a bridge carries tool data and tool calls between the host and embedded view.

**Tech Stack:** Markdown, YAML frontmatter, Devbox, Git, GitHub CLI.

---

### Task 1: Write `research/mcp-apps.md`

- [ ] Add valid frontmatter with MCP Apps sources, tags `[inter-agent-comms, governance, ecosystem-survey]`, and `cf_areas: [capi, uaa, diego]`.
- [ ] Explain the `ui://` resource, tool declaration, host fetch/render flow, sandboxed iframe, and bidirectional communication.
- [ ] Cover SDK roles for view authors, hosts, and MCP server authors, plus the distinction between the official extension and optional host SDKs.
- [ ] Assess security boundaries: iframe sandbox, host capabilities, content security policy, origin/resource trust, tool authorization, and sensitive data.
- [ ] Assess CF relevance for hosted MCP services, gateways, bindings, identity, isolation, and audit.
- [ ] Add questions about host compatibility, tenancy, resource delivery, versioning, policy, and observability.

### Task 2: Validate and publish

- [ ] Run `devbox run validate`, `devbox run test`, and `git diff --check`.
- [ ] Stage only the note and approved spec/plan, commit `docs: add MCP Apps research note`, push `research/mcp-apps`, and open a checklist-complete PR targeting `main`.
- [ ] Verify PR metadata and CI with `gh pr view`.
