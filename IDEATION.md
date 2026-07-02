# Ideation Brief — Agentic Runtime Research Phase

**Status:** Proposed (this brief is itself under review — feedback welcome on the PR).
**Working group:** [Cloud Foundry Agentic Runtime](https://github.com/cloudfoundry/community/blob/main/toc/working-groups/agentic-runtime.md)

## Why this phase exists

The Agentic Runtime Working Group is new, and the design space — running AI agents and
LLM-powered workloads as first-class citizens on Cloud Foundry — is broad and moving fast.
Before committing to specific designs or RFCs, we want to map the landscape together:
gather what the community already knows and surface prior art from the wider ecosystem.
With that map in hand, the workshop can then see where Cloud Foundry's primitives help or
fall short.

This repository is the home for that research. It is deliberately **lightweight and
open**: the goal is breadth of input from anyone interested, not polished deliverables.

## The four-phase roadmap

This research phase is step one of four:

1. **Capture & research (now, ~a few weeks).** Contributors open pull requests with either
   a quick **idea** in [`ideas/`](./ideas) — a spark, question, or pointer, at a low bar —
   or a short, sourced **research note** in [`research/`](./research). We want broad,
   *outward-looking* coverage of the wider agentic ecosystem — relevant technologies, prior
   art, and how others solve these problems. Where Cloud Foundry fits comes later. Ideas and
   research link together — one research note can back several ideas — and an idea with enough
   research behind it can grow into a proposal.
2. **Workshop.** The working group meets to read across the accumulated notes and cluster
   them into **themes**. Themes are *not* defined up front — they emerge from what people
   actually contribute.
3. **Match.** Working-group members align their interests with the identified themes and
   form small groups around them.
4. **POC / RFC.** Each theme group spins up focused work — proofs-of-concept and Cloud
   Foundry RFCs — feeding the platform roadmap.

We are building only what Phase 1 needs right now. Structure for themes, POCs, and RFCs
will be added once the workshop has shaped it.

## What to contribute in Phase 1

**Look outward.** Phase 1 is about understanding the wider agentic and AI ecosystem — not
about cataloguing Cloud Foundry. Where Cloud Foundry's primitives help or fall short is
something we want to *discover* at the workshop, drawn from this research, rather than
assume up front.

**Two ways in.** Not everything needs to be a polished note. If you have a spark but no
time to write it up, drop it in [`ideas/`](./ideas) — we'd rather capture it than turn it
away for not being a full research note. A sourced, structured write-up belongs in
[`research/`](./research). The scope below applies to both.

**In scope** — research notes that inform the design space, such as:

- Analyses of agent frameworks, protocols, and platforms (how others solve a problem).
- Prior art and standards — identity, sandboxing, observability, orchestration conventions.
- How adjacent runtimes and platforms (Kubernetes, serverless, other PaaS) handle agentic
  workloads.
- Surveys of the surrounding ecosystem and where it's heading.

**Out of scope for now:**

- Finished solutions, designs, or RFCs — those come in Phase 4, after the workshop. A note
  may *raise* questions and point at possible directions, but its job is to inform, not to
  settle on a final answer.
- Definitive Cloud Foundry gap lists. Identifying gaps is an **outcome** of this phase,
  synthesized at the workshop from the body of research — not a starting point any one
  contributor supplies.

## What makes a good research note

- **Sourced.** Link to the primary material so others can dig in.
- **Summarized.** A few sentences capturing the essence — assume the reader is busy.
- **Outward-looking, with a light CF lens.** The substance is the external research; add a
  short note on why it might matter for Cloud Foundry. A loose or speculative connection is
  fine — "not sure how this maps yet" is a perfectly good answer.
- **Honest about open questions.** Unknowns are valuable signal for the workshop.

Each note follows a small template — see [`research/TEMPLATE.md`](./research/TEMPLATE.md).
[`CONTRIBUTING.md`](./CONTRIBUTING.md) explains the mechanics.

## Tagging: how themes will emerge

Each note carries free-form `tags` in its frontmatter. At the workshop we'll use these
tags to cluster notes into themes — so tagging well is how you influence the agenda.

Tags are **descriptive, not prescriptive.** To reduce noise, here is a *non-binding*
starting vocabulary drawn from the working-group charter. Use these where they fit, and
invent new ones where they don't:

- `identity` — workload/agent identity, authn, authz
- `runtime-lifecycle` — how agents are deployed, started, stopped, resumed
- `sandboxing-isolation` — execution isolation, policy enforcement
- `orchestration` — multi-step / multi-agent coordination
- `inter-agent-comms` — agent-to-agent and agent-to-tool protocols
- `observability-governance` — telemetry, audit, compliance
- `autoscaling` — event-driven and scale-to-zero patterns
- `ecosystem-survey` — landscape scans of tools, frameworks, vendors

**These are hints, not buckets.** Don't file your note into a predetermined theme — just
describe it accurately and let the themes emerge.

## Timeline

Specific dates (the research window length and the workshop date) are set at the
working-group kickoff and announced in
[#ai-wg](https://cloudfoundry.slack.com/archives/C0B214KJ1HA) on Slack. Expect the research
window to run a few weeks.

## How to participate

1. Read [`CONTRIBUTING.md`](./CONTRIBUTING.md).
2. Add an idea or a research note using the matching template, and open a PR.
3. Join the conversation in [#ai-wg](https://cloudfoundry.slack.com/archives/C0B214KJ1HA).

## Feedback on this process

This brief is part of the first pull request *on purpose* — so the working group can shape
the process before research arrives at volume. If something here doesn't serve the goal,
say so on the PR.
