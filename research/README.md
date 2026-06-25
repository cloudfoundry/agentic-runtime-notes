# Research notes

This directory holds the working group's research notes for the current research phase
(see [`../IDEATION.md`](../IDEATION.md)).

The directory is intentionally **flat**: every note is a single Markdown file here, with
metadata in YAML frontmatter. We do **not** sort notes into topic folders — themes are
identified later, at the workshop, by clustering on tags. Filing notes into folders now
would pre-impose the very themes we want to let emerge.

## Adding a note

Copy [`TEMPLATE.md`](./TEMPLATE.md), rename it to a kebab-case topic (`my-topic.md`), and
fill it in. See [`cf-runtime-gaps.md`](./cf-runtime-gaps.md) for a complete example, and
[`../CONTRIBUTING.md`](../CONTRIBUTING.md) for the full workflow.

## Frontmatter schema

Each note begins with a YAML frontmatter block:

```yaml
---
title: Cloud Foundry gaps for AI agents
author: Ruben Koster (@rkoster)
date: 2026-06-25
tags: [ecosystem-survey, autoscaling, identity]
cf_areas: [diego, capi, uaa, loggregator]
status: draft
sources:
  - https://example.com/source-one
---
```

| Field | Required | Description |
|-------|----------|-------------|
| `title` | yes | Concise human-readable title. |
| `author` | yes | `Name (@github-handle)`. |
| `date` | yes | `YYYY-MM-DD`, the date the note was written. |
| `tags` | yes | List of free-form tags. Drives theme clustering — see the suggested vocabulary in [`../IDEATION.md`](../IDEATION.md#tagging-how-themes-will-emerge). |
| `cf_areas` | no | List of related Cloud Foundry components (e.g. `diego`, `capi`, `uaa`, `bosh`, `loggregator`). |
| `status` | yes | `draft` or `reviewed`. |
| `sources` | yes | List of URLs to the primary material. |

## Body structure

After the frontmatter, use these four sections:

```markdown
## Summary

Two to four sentences capturing the essence.

## Key findings

- Bullet points with the substantive takeaways.

## CF relevance

How this maps to Cloud Foundry primitives or gaps — including "it doesn't map cleanly, and
here's why."

## Open questions

- Unresolved questions worth raising at the workshop.
```

A CI check validates that every note has valid frontmatter, a kebab-case filename, and
these four sections.
