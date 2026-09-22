# Agent Router Research Note Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add and publish a sourced architecture-first research note on Agent Router and its relevance to Cloud Foundry.

**Architecture:** Create one flat Markdown note under `research/`, following the repository template. The note will separate upstream facts from Cloud Foundry analysis and will use Agent Router's control-plane/data-plane architecture as its organizing model.

**Tech Stack:** Markdown, YAML frontmatter, repository note validator, Python tests, GitHub CLI.

---

### Task 1: Create the research note

**Files:**
- Create: `research/agent-router.md`

- [ ] **Step 1: Add valid frontmatter**

Use `title: Agent Router: Envoy-Based Control Plane for AI Traffic`, author `Ruben Koster (@rkoster)`, date `2026-09-17`, tags covering `routing`, `observability-governance`, `ecosystem-survey`, and `agent-runtime`, `cf_areas: []`, and `status: draft`. Add ratings from 0-100 with one-sentence explanations and link the upstream repository, Apache license, README, concepts, system architecture, control plane, data plane, resources, getting started, and CLI documentation.

- [ ] **Step 2: Write the Summary section**

Explain that Agent Router, formerly Envoy AI Gateway, is an Apache-2.0 open-source control plane for AI and agent traffic. State that it exposes an OpenAI-compatible interface while centralizing provider routing, credentials, quotas, failover, and usage attribution, and that its production architecture is Kubernetes- and Envoy-based with a standalone CLI option.

- [ ] **Step 3: Write the Key findings section**

Cover these concrete findings as sourced bullets:

1. The control plane watches `AIGatewayRoute`, `AIServiceBackend`, and `BackendSecurityPolicy` resources, creates or manages standard Envoy Gateway resources, and fine-tunes xDS through the Envoy Gateway extension server.
2. The data plane is Envoy Proxy plus the AI Gateway External Processor and Rate Limit Service; the processor selects providers, transforms request and response formats, manages upstream authentication, tracks tokens, and supports streaming and non-streaming responses.
3. `AIGatewayRoute` defines the unified client-facing API and routing, `AIServiceBackend` represents a provider or service endpoint, and `BackendSecurityPolicy` supplies API-key or AWS credential behavior.
4. The gateway supports hosted providers, self-hosted inference, and MCP servers behind a consistent interface, including a two-tier pattern for centralized entry routing and self-hosted model clusters.
5. `aigw run` can run locally without Kubernetes or Docker, while production deployment uses Kubernetes and Envoy Gateway; the configuration model is intended to carry between these modes.
6. The architecture is an AI-aware gateway and policy layer, not an agent workflow engine or durable execution runtime; it does not replace application-level orchestration, memory, or task recovery.

- [ ] **Step 4: Write the CF relevance section**

Assess the architecture against Cloud Foundry without claiming existing integration. Explain that CF could expose Agent Router as a shared platform service or a dedicated gateway app, with service bindings carrying endpoint and client credentials while platform operators retain provider credentials. Map Envoy's edge routing and policy role to CF routing and platform-managed ingress, but note that token-aware rate limiting and model-aware transformations are beyond ordinary HTTP routing. Discuss operational trade-offs: the standalone binary is easier to run as a CF app, while the controller, CRDs, admission webhooks, xDS, and sidecar injection assume Kubernetes and would need a replacement control plane or an external Kubernetes installation. Mention that shared gateway observability could provide cost and usage attribution, but the platform would need explicit log, metric, trace, and tenant isolation choices.

- [ ] **Step 5: Write the Open questions section**

Ask whether CF should host one shared AI gateway, offer a brokered/bound gateway service, or leave routing to application teams; whether provider credentials and quotas should be platform-managed; whether token-aware limits and cost attribution belong in the platform; whether Kubernetes should remain a dependency for the full Agent Router architecture; and which interoperability boundary CF should standardize on for OpenAI-compatible APIs, MCP, and future agent protocols.

### Task 2: Validate the note

**Files:**
- Test: `tests/test_workflows.py`
- Test: `.github/scripts/validate_notes.py`

- [ ] **Step 1: Run the note validator**

Run:

```bash
python .github/scripts/validate_notes.py
```

Expected: successful validation with no template placeholders, valid YAML frontmatter, a lowercase kebab-case filename, and all four required sections.

- [ ] **Step 2: Run the test suite**

Run:

```bash
pytest -q
```

Expected: all tests pass, including tests that parse and validate research-note metadata.

- [ ] **Step 3: Inspect the diff**

Run:

```bash
git diff --check
git status --short
git diff -- research/agent-router.md
```

Expected: no whitespace errors; only the intended research note and approved design/plan documents are reviewed for staging, while unrelated untracked environment artifacts remain untouched.

### Task 3: Commit the note and create the PR

**Files:**
- Modify: `research/agent-router.md`
- Include: `docs/superpowers/specs/2026-09-17-agent-router-research-note-design.md`
- Include: `docs/superpowers/plans/2026-09-17-agent-router-research-note.md`

- [ ] **Step 1: Create a feature branch**

Run:

```bash
git switch -c research/agent-router
```

Expected: the new branch is based on the current `main` branch and contains no unrelated staged files.

- [ ] **Step 2: Stage only intended files**

Run:

```bash
git add research/agent-router.md docs/superpowers/specs/2026-09-17-agent-router-research-note-design.md docs/superpowers/plans/2026-09-17-agent-router-research-note.md
git diff --cached --check
git status --short
```

Expected: only the three listed files are staged.

- [ ] **Step 3: Commit the research note**

Run:

```bash
git commit -m "docs: add Agent Router research note"
```

Expected: one commit containing the research note and its approved design artifacts.

- [ ] **Step 4: Push and open the PR**

Run:

```bash
git push -u origin research/agent-router
```

Before submitting, replace the PR template comments with a concise description and check every checklist item. The PR should target `main`, contain only the note and approved planning artifacts, and link the upstream Agent Router sources through the note itself.

- [ ] **Step 5: Verify the created PR**

Run:

```bash
gh pr view --json number,url,title,baseRefName,headRefName,state,statusCheckRollup
```

Expected: an open PR from `research/agent-router` into `main`, with CI checks reported and the final URL recorded for the user.
