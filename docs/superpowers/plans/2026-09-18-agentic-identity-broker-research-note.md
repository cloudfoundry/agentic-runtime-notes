# Agentic Identity Broker Research Note Implementation Plan

> **For agentic workers:** Execute this plan inline with validation checkpoints.

**Goal:** Add and publish a sourced research note on Agentic Identity Broker as delegated OAuth and credential mediation infrastructure.

**Architecture:** Describe the broker's consent/grant model, trusted proxy boundary, dual-port Go service, encrypted token vault, and RFC 8693 gateway exchange. Map these capabilities to CF identity, bindings, service policy, agent/tool authorization, and audit.

**Tech Stack:** Markdown, YAML frontmatter, Devbox, Git, GitHub CLI.

---

### Task 1: Write `research/agentic-identity-broker.md`

- [ ] Add frontmatter with title `Agentic Identity Broker: Delegated OAuth and Credential Mediation`, author `Ruben Koster (@rkoster)`, date `2026-09-18`, tags `[authorization, identity, observability-governance, ecosystem-survey]`, `cf_areas: [uaa, capi, diego, loggregator]`, `status: draft`, ratings, and official website/concept/API sources.
- [ ] Explain principal, agent, third-party service, permission set, grant, and user-session objects, including expiry and revocation.
- [ ] Describe the trusted reverse-proxy authentication boundary and dual-port service topology for end-user versus admin surfaces.
- [ ] Cover consent UI, encrypted token storage with envelope encryption, and the rule that agents do not receive long-lived provider credentials.
- [ ] Explain RFC 8693 token exchange, resource-based provider selection, gateway client assertions, and audit identities.
- [ ] Assess CF relevance for UAA, instance identity, service bindings, service brokers, agent/tool authorization, credential rotation, and Loggregator.
- [ ] Add open questions about canonical agent identity, delegated authority, token exchange placement, revocation latency, service policy, and audit/privacy.

### Task 2: Validate and publish

- [ ] Run `devbox run validate`, `devbox run test`, and `git diff --check`.
- [ ] Stage only the note and approved spec/plan, commit `docs: add Agentic Identity Broker research note`, push `research/agentic-identity-broker`, and open a checklist-complete PR targeting `main`.
- [ ] Verify PR metadata and CI with `gh pr view`.
