# RFC 8693 Token Exchange Research Note Implementation Plan

> **For agentic workers:** Execute this plan inline with validation checkpoints.

**Goal:** Add and publish a sourced research note on RFC 8693 OAuth 2.0 Token Exchange for delegated agent authority.

**Architecture:** Explain the STS exchange request/response, subject and actor tokens, targeting parameters, impersonation/delegation claims, and policy boundary. Map the protocol to CF identity and service-to-service authorization.

**Tech Stack:** Markdown, YAML frontmatter, Devbox, Git, GitHub CLI.

---

### Task 1: Write `research/rfc-8693-token-exchange.md`

- [ ] Add frontmatter with title `RFC 8693: OAuth 2.0 Token Exchange for Delegated Agent Authority`, author `Ruben Koster (@rkoster)`, date `2026-09-18`, tags `[authorization, identity, inter-agent-comms, ecosystem-survey]`, `cf_areas: [uaa, capi, diego]`, `status: draft`, ratings, and RFC 8693/RFC Editor sources.
- [ ] Explain RFC 8693 as an IETF Proposed Standard defining an HTTP/JSON Security Token Service protocol.
- [ ] Cover token exchange parameters including grant type, subject token, actor token, resource, audience, scope, and requested token type.
- [ ] Distinguish impersonation, where the issued subject acts as the original subject, from delegation, where `sub` and `act` preserve the principal and current actor; cover `may_act` authorization.
- [ ] Explain that RFC 8693 provides protocol mechanics but authorization policy, trust in token issuers, key validation, and resource policy remain deployment responsibilities.
- [ ] Assess CF relevance for UAA, instance identity, service bindings, agent gateways, service-to-service calls, least privilege, and audit.
- [ ] Add open questions about subject/actor mapping, audience/resource policy, token lifetime, revocation, nested delegation, and audit semantics.

### Task 2: Validate and publish

- [ ] Run `devbox run validate`, `devbox run test`, and `git diff --check`.
- [ ] Stage only the note and approved spec/plan, commit `docs: add RFC 8693 token exchange research note`, push `research/rfc-8693-token-exchange`, and open a separate checklist-complete PR targeting `main`.
- [ ] Verify PR metadata and CI with `gh pr view`.
