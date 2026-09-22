# Reactive Agents Research Note Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add and publish a sourced comparative research note on Infinity/RAP, MCP Tasks, and MCP Triggers & Events, including Cloud Foundry relevance.

**Architecture:** Create one flat Markdown note under `research/`, following the repository template. Organize it around three related layers: Infinity/RAP reactive execution, MCP Tasks durable task state, and experimental MCP Triggers & Events delivery. Compare their semantics and map the resulting requirements to Cloud Foundry capabilities and gaps.

**Tech Stack:** Markdown, YAML frontmatter, Devbox, repository note validator, Git, GitHub CLI.

---

### Task 1: Create the comparative reactive agents research note

**Files:**
- Create: `research/infinity.md`

- [ ] **Step 1: Add valid frontmatter**

Use `title: "Reactive Agents: Infinity/RAP and MCP Asynchronous Extensions"`, author `Ruben Koster (@rkoster)`, date `2026-09-17`, tags covering `orchestration`, `durable-execution`, `inter-agent-comms`, `event-driven`, and `ecosystem-survey`, `cf_areas: [capi, diego, loggregator]`, and `status: draft`. Add provisional ratings from 0-100 with concise justifications. Link the Infinity repository, README, runtime overview, runtime architecture, RAP overview, RAP specification overview, and Lambda deployment documentation; the MCP Tasks repository and README; and the MCP Triggers & Events repository, README, and design sketch.

- [ ] **Step 2: Write the Summary section**

Explain that Infinity is a Rust framework for highly concurrent agents and the reference runtime for RAP. State that it models work as short execution slices: load durable state, process a message and model completion, dispatch asynchronous tool calls, persist state, and yield. Introduce MCP Tasks as an official extension for durable call-now/fetch-later task state, and Triggers & Events as explicitly experimental work on proactive server notifications. Mention that MCP compatibility preserves existing synchronous tools while these extensions and RAP target long-running and event-driven work.

- [ ] **Step 3: Write the Key findings section**

Cover these sourced findings as bullets:

1. Every Infinity input is an `InputMessage`, including user text, tool results, subscription events, child-thread reports, OAuth challenges, and timer wake-ups; a `group_id` identifies the conversation thread.
2. An Infinity slice loads conversation history and processed-message state, prepares and deduplicates inputs, runs a model completion, dispatches a tool call, persists state, and ends without waiting on external work.
3. RAP uses HTTP POST messages: the runtime sends a tool invocation with a callback URL, the tool acknowledges immediately, and later posts a result or event back to the runtime. The callback becomes the next wake-up message.
4. RAP makes long-running calls, subscriptions, webhooks, human approvals, and hibernating agents first-class. When no work is pending, the agent process can shut down and resume when a message arrives.
5. RAP uses per-thread ordering and durable state to tolerate at-least-once delivery, redelivery, restarts, and cold starts; the note should identify ordering and deduplication as important implementation mechanisms rather than assume exactly-once execution.
6. The MCP Tasks extension defines durable task state machines with receiver-generated task IDs, status inspection, polling, and deferred result retrieval. The repository identifies `2026-07-28` as a stable schema snapshot and the extension as based on SEP-2663.
7. MCP Triggers & Events is explicitly experimental. Its working group explores `events/list`, poll, stream, and webhook delivery modes, subscription TTLs, cursors and replay, event IDs for deduplication, webhook signatures, and cross-transport ordering guarantees; its draft design is not an official MCP recommendation.
8. MCP remains useful for fast request/response tools, and Infinity can run MCP servers through a compatibility layer. RAP changes the waiting contract, MCP Tasks adds task lifecycle state, and Triggers & Events explores proactive event delivery; these primitives overlap but are not interchangeable.
9. Infinity's Lambda deployment maps one slice to a short-lived invocation, with SQS FIFO for ordered input, Aurora DSQL for durable state, Bedrock for model calls, and a receiver Lambda for RAP callbacks. This is an Infinity deployment architecture, not a Cloud Foundry integration.
10. Infinity, RAP, and the MCP extensions address asynchronous agent/tool interaction, not provider routing, general application ingress, or every workflow orchestration concern.

- [ ] **Step 4: Write the CF relevance section**

Map the three approaches to Cloud Foundry explicitly as analysis. Explain that Diego is well suited to supervising resident Infinity processes, but reactive hibernation and scale-to-zero need a message-triggered activation mechanism that ordinary CF application routing does not provide. CAPI could manage an agent application and its binding metadata, while an external queue and durable state store would be required for wake-ups, ordering, and persistence. Discuss whether a CF-managed callback/event receiver or brokered event gateway could translate RAP callbacks, MCP task completions, and MCP event webhooks into queue messages. Include Loggregator implications for correlating one logical agent turn across multiple short processes, tool callbacks, retries, polling, and asynchronous events. Note that applications on CF could run the Infinity Rust library or a compatible MCP service, but a platform offering would need callback authentication, tenant isolation, delivery/retry policies, replay behavior, task/event state, and state-store integration.

- [ ] **Step 5: Write the Open questions section**

Ask whether CF should provide a common durable input/event substrate for reactive agents; whether it should expose RAP, MCP Tasks, MCP Triggers & Events, or an implementation-neutral abstraction; how callback and webhook authentication and tenant routing should work; which delivery, ordering, deduplication, replay, and retry guarantees the platform should expose; whether CF should support scale-to-zero activation or focus on resident processes; how task state, subscriptions, state stores, and timers should be provisioned; how asynchronous usage should appear in Loggregator and billing; and whether RAP should be adopted independently of Infinity's Rust runtime.

### Task 2: Validate the note

**Files:**
- Test: `.github/scripts/validate_notes.py`
- Test: `devbox.json`

- [ ] **Step 1: Run configured validation**

Run:

```bash
devbox run validate
```

Expected: successful validation with all research notes and ideas reported valid, including `research/infinity.md`.

- [ ] **Step 2: Run configured test script**

Run:

```bash
devbox run test
```

Expected: the same note validation completes successfully through the repository's configured test script.

- [ ] **Step 3: Inspect the diff**

Run:

```bash
git diff --check
```

Expected: no whitespace errors; only the intended note and approved design/plan artifacts are staged, while unrelated environment artifacts remain untouched.

### Task 3: Commit the note and create the PR

**Files:**
- Create: `research/infinity.md`
- Include: `docs/superpowers/specs/2026-09-17-infinity-research-note-design.md`
- Include: `docs/superpowers/plans/2026-09-17-infinity-research-note.md`

- [ ] **Step 1: Stage only intended files**

Run:

```bash
git add research/infinity.md
```

Expected: only the comparative note and its approved design/plan documents are staged.

- [ ] **Step 2: Commit the note**

Run:

```bash
git commit -m "docs: add reactive agents research note"
```

Expected: one commit containing the research note and approved planning artifacts.

- [ ] **Step 3: Push the branch**

Run:

```bash
git push -u origin research/infinity
```

Expected: the `research/infinity` branch is available on origin without unrelated files.

- [ ] **Step 4: Open the PR**

Run:

```bash
gh pr create --base main --head research/infinity --title "docs: add reactive agents research note" --body-file /tmp/infinity-pr-body.md
```

The PR body must describe Infinity/RAP, MCP Tasks, MCP Triggers & Events, the comparison, and Cloud Foundry relevance, and confirm the repository checklist.

- [ ] **Step 5: Verify the PR**

Run:

```bash
gh pr view --json number,url,title,baseRefName,headRefName,state,statusCheckRollup
```

Expected: an open PR from `research/infinity` into `main`, with the validation check visible and the final URL recorded for the user.
