# MCP Apps Research Note Design

## Goal

Capture a sourced research note on MCP Apps as the official MCP extension for interactive UIs
served by MCP servers and embedded in compliant AI hosts.

## Scope

Cover `ui://` resources, tool metadata, sandboxed iframe rendering, host/UI bidirectional
communication, SDK roles, host capability boundaries, security, and current ecosystem maturity.
Assess CF relevance for hosted MCP services, gateway policy, service bindings, identity,
network isolation, and audit of interactive tool use.

## Structure and evidence

Create `research/mcp-apps.md` with the required four sections and frontmatter. Use the MCP Apps
repository, README, specification, API docs, and examples. Clearly distinguish the official
extension/specification from optional host implementations and label CF conclusions as analysis.

## Validation

Run Devbox validation and tests, inspect whitespace/staged files, commit the note and plan on
`research/mcp-apps`, push, and open a PR targeting `main` without unrelated artifacts.
