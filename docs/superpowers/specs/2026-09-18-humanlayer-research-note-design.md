# HumanLayer Research Note Design

## Goal

Add a sourced research note on HumanLayer's multiplayer agent workspace and its support for
stateless-at-the-process-layer agent execution.

## Scope

The note will describe HumanLayer's API/control-plane and local or remote daemon model, task
grouping, sessions, artifacts, plans, diffs, worktrees, event streaming, and multi-user access.
It will assess the thesis that durable collaboration/session state can be externalized while
agent processes and hosts remain replaceable.

The note will explicitly distinguish documented daemon reconnection and externalized events from
unproven live process migration between containers. It will discuss host-bound capabilities such
as code, credentials, tools, private network access, worktrees, and persistent daemon storage.
Cloud Foundry analysis will cover CAPI/Diego, durable state stores, disposable processes, identity,
workspaces, and Loggregator.

## Structure and evidence

Create `research/humanlayer.md` with the required four sections and frontmatter. Use the
HumanLayer repository, current website, remote daemon guide, remote daemon architecture docs,
and related public documentation. Clearly distinguish current product claims from architectural
inference.

## Validation

Run Devbox validation and tests, inspect whitespace/staged files, commit the note and plan on
`research/humanlayer`, push, and open a PR targeting `main` without unrelated artifacts.
