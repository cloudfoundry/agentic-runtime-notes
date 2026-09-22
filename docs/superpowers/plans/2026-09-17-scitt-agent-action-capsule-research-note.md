# SCITT Agent Action Capsule Research Note Implementation Plan

> **For agentic workers:** Execute this plan inline with validation checkpoints.

**Goal:** Add and publish a sourced research note on SCITT and Agent Action Capsule for verifiable agent-action provenance in Cloud Foundry.

**Architecture:** Explain SCITT as the transparency and receipt layer, and Agent Action Capsule as an individual Internet-Draft profile for digest-committed action statements and COSE producer envelopes. Map certificate-backed CF workload identity and platform events to provenance records without claiming existing integration.

**Tech Stack:** Markdown, YAML frontmatter, Devbox, Git, GitHub CLI.

---

### Task 1: Write the research note

**Files:**
- Create: `research/scitt-agent-action-capsule.md`

- [ ] Add frontmatter with title `SCITT and Agent Action Capsule: Verifiable Agent-Action Provenance`, author `Ruben Koster (@rkoster)`, date `2026-09-17`, tags `[observability-governance, authorization, identity, ecosystem-survey]`, `cf_areas: [uaa, capi, diego, loggregator]`, `status: draft`, provisional ratings, and SCITT/Agent Action Capsule/Datatracker sources.
- [ ] Explain SCITT's transparency-service role and separate it from the Agent Action Capsule statement profile.
- [ ] Cover capsule canonicalization, digest identity, chain, verdict/refusal records, COSE_Sign1 producer envelopes, signer-independent identity, and Class-1/envelope/receipt verification.
- [ ] State that SCITT architecture and receipt specifications are RFCs while Agent Action Capsule is an individual Internet-Draft, not an adopted WG document or RFC.
- [ ] Analyze a CF boundary where a gateway verifies an instance identity certificate, records agent identity and authorization context, emits a capsule, and submits/registers evidence with a transparency service.
- [ ] Discuss UAA/CAPI/Diego event correlation, Loggregator/audit integration, privacy and redaction, receipt availability, signer authorization, revocation, and non-repudiation.
- [ ] Add open questions about subject identity, policy evidence, refusal semantics, retention, tenant isolation, and verifier trust.

### Task 2: Validate and publish

- [ ] Run `devbox run validate`, `devbox run test`, and `git diff --check`.
- [ ] Stage only the note and approved spec/plan, commit `docs: add SCITT agent action capsule research note`, push `research/scitt-agent-action-capsule`, and open a checklist-complete PR targeting `main`.
- [ ] Verify PR metadata and CI with `gh pr view`.
