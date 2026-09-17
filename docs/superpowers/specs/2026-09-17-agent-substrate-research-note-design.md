# Agent Substrate Research Note Design

## Goal

Capture a first-pass, sourced research note on Agent Substrate's architecture and potential
relevance to Cloud Foundry, with later refinement intentionally left open.

## Scope

The note will cover Agent Substrate's actor/worker model, lifecycle control, suspend/resume
and snapshotting, sandbox backends, network routing, Kubernetes integration, and the boundary
between implemented demonstrations and aspirational architecture. It will briefly assess
Cloud Foundry implications for Diego, CAPI, routing, workload isolation, density, and state
management.

## Structure

Create `research/agent-substrate.md` using the repository template and required sections:

1. Summary
2. Key findings
3. CF relevance
4. Open questions

Use concise provisional ratings and label this as a research snapshot. Do not present Agent
Substrate as an officially supported Google product or claim that aspirational architecture is
already implemented.

## Sources and evidence

Use the Agent Substrate repository README, architecture document, command/component tour,
observability or API documentation when available, and the counter demo. Claims about Cloud
Foundry will be analysis or open questions, not claims of existing integration.

## Validation

Run the repository's configured Devbox validation and test scripts, inspect whitespace and
the staged diff, then commit the note and this approved design spec on `research/agent-substrate`.
Push the branch and open a new PR targeting `main` without staging unrelated environment
artifacts.
