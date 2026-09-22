# Agent Baseline Research Note Design

## Goal

Add a sourced research note on Agent Baseline as an open draft security framework for enterprise
AI agents.

## Scope

The note will explain the six outcomes: Discover, Constrain, Authorize, Observe, Validate, and
Respond, along with the 35 controls and evidence-oriented framing. It will treat the project as
a working draft for public comment, not a finalized standard.

The Cloud Foundry analysis will map the outcomes to CAPI/Diego inventory and lifecycle, UAA and
workload identity, sandbox/network policy, authorization, Loggregator/audit, build and release
validation, revocation, quarantine, and incident response. It will identify where CF supplies
primitives and where agent-specific controls remain missing.

## Structure and evidence

Create `research/agent-baseline.md` with the required four sections and frontmatter. Use the
Agent Baseline website, controls, white paper, source repository, and public-comment status.
Clearly distinguish framework requirements from existing CF capabilities and label mappings as
analysis or open questions.

## Validation

Run Devbox validation and tests, inspect whitespace/staged files, commit the note and plan on
`research/agent-baseline`, push, and open a PR targeting `main` without unrelated artifacts.
