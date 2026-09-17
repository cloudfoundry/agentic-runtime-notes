# WebMCP Research Note Design

## Goal

Capture a sourced research note on WebMCP as a browser-native way for web applications to
expose page functionality as agent tools.

## Scope

Cover WebMCP's imperative JavaScript and declarative HTML form APIs, the browser as the
execution and identity context, the distinction from backend MCP integrations, implementation
status, and security-minded tool design. Assess Cloud Foundry relevance for applications that
want agents to act through existing authenticated web sessions without duplicating backend
integrations.

## Structure and evidence

Create `research/webmcp.md` with the required four sections and frontmatter. Use the WebMCP
repository, README, explainer, implementation status, and security guidance. Distinguish the
proposal/experimental status from deployed browser behavior and label CF analysis as proposed
integration.

## Validation

Run Devbox validation and tests, inspect whitespace/staged files, commit the note and plan on
`research/webmcp`, push, and open a PR targeting `main` without unrelated artifacts.
