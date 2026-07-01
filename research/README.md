# Research notes

This directory holds the working group's research notes for the current research phase
(see [`../IDEATION.md`](../IDEATION.md)).

The directory is intentionally **flat**: every note is a single Markdown file here, with
metadata in YAML frontmatter. We do **not** sort notes into topic folders — themes are
identified later, at the workshop, by clustering on tags. Filing notes into folders now
would pre-impose the very themes we want to let emerge.

## Adding a note

Copy [`TEMPLATE.md`](./TEMPLATE.md), rename it to a kebab-case topic (`my-topic.md`), and
fill it in. See [`../CONTRIBUTING.md`](../CONTRIBUTING.md) for the full workflow.

Not ready for a sourced write-up? Drop a spark in [`../ideas/`](../ideas) instead — it can
graduate into a research note later.

## Frontmatter schema

Each note begins with a YAML frontmatter block:

```yaml
---
title: How LangGraph models multi-agent orchestration
author: Jane Doe (@janedoe)
date: 2026-06-25
tags: [orchestration, inter-agent-comms, ecosystem-survey]
cf_areas: [diego, capi]
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

A short, light-touch note on why this might matter for Cloud Foundry. A loose or
speculative connection is fine — including "not sure how this maps yet." Synthesizing the
research into concrete Cloud Foundry gaps is the workshop's job, not something each note
has to settle.

## Open questions

- Unresolved questions worth raising at the workshop.
```

A CI check validates that every note has valid frontmatter, a kebab-case filename, and
these four sections.
