# MCP Filesystems Research Note Design

## Goal

Add a sourced research note on the MCP Filesystems Working Group's proposal to make Resources
bidirectional for agent workflows.

## Scope

The note will cover the group's mission, proposed create/update/delete/stat operations,
optimistic concurrency control, change notifications, cache metadata, and its relationship to
existing MCP Resources and filesystem-like URIs. It will distinguish remote MCP resource
semantics from host-side filesystem materialization and authorization, which the charter leaves
out of scope.

The Cloud Foundry analysis will consider agent workspaces, object/blob-backed resources,
service bindings, concurrent writers, cache invalidation, audit, and authorization boundaries.
It will identify the work as early-stage: the charter lists the main SEP as ideating.

## Structure and evidence

Create `research/mcp-filesystems.md` with the required four sections and frontmatter. Use the
official MCP Filesystems charter, MCP Resources specification, relevant SEP links listed by the
charter, and the reference filesystem server where useful. Label CF conclusions as analysis or
open questions.

## Validation

Run Devbox validation and tests, inspect whitespace/staged files, commit the note and plan on
`research/mcp-filesystems`, push, and open a PR targeting `main` without unrelated artifacts.
