# RFC 8628 Device Authorization Research Note Implementation Plan

> **For agentic workers:** Execute this plan inline with validation checkpoints.

**Goal:** Add and publish a sourced research note on RFC 8628 OAuth 2.0 Device Authorization Grant for headless agents and remote workloads.

**Architecture:** Explain the device authorization endpoint, user/device codes, secondary-device consent, polling and token issuance, then map the flow to CF UAA, remote daemons, bindings, and audit while separating initial consent from downstream delegation.

**Tech Stack:** Markdown, YAML frontmatter, Devbox, Git, GitHub CLI.

---

### Task 1: Write `research/rfc-8628-device-authorization.md`

- [ ] Add frontmatter with title `RFC 8628: Device Authorization for Headless Agents and Remote Workloads`, author `Ruben Koster (@rkoster)`, date `2026-09-18`, tags `[identity, authorization, orchestration, ecosystem-survey]`, `cf_areas: [uaa, capi, diego]`, `status: draft`, ratings, and RFC 8628/RFC Editor sources.
- [ ] Explain the constrained/headless client problem and the secondary-device authorization flow.
- [ ] Cover device authorization request, device code, user code, verification URI, expiry, polling interval, token request, and errors such as `authorization_pending`, `slow_down`, `access_denied`, and `expired_token`.
- [ ] Cover discovery and client authentication/public-client behavior.
- [ ] Explain brute-force, phishing, device trust, polling overload, user consent, and token storage security considerations.
- [ ] Assess CF relevance for UAA, headless CLIs, remote agent daemons, service bindings, user consent, token persistence, revocation, and audit.
- [ ] Distinguish device authorization from RFC 8693 token exchange and agent delegation; add open questions about device identity, polling, binding, and revocation.

### Task 2: Validate and publish

- [ ] Run `devbox run validate`, `devbox run test`, and `git diff --check`.
- [ ] Stage only the note and approved spec/plan, commit `docs: add RFC 8628 device authorization research note`, push `research/rfc-8628-device-authorization`, and open a checklist-complete PR targeting `main`.
- [ ] Verify PR metadata and CI with `gh pr view`.
