# Contributing

Thanks for helping shape the future of agentic workloads on Cloud Foundry. During the
current **research phase**, contributions take the form of **research notes** added to
[`research/`](./research) via pull requests.

For the why and the bigger picture, read [`IDEATION.md`](./IDEATION.md).

## Quick start

1. **Fork** this repository (or, if you're a working-group member with write access, create
   a branch).
2. **Copy the template:**
   ```bash
   cp research/TEMPLATE.md research/my-topic.md
   ```
3. **Fill it in.** Keep it short, sourced, and outward-looking (see
   [`IDEATION.md`](./IDEATION.md) for what Phase 1 is after). See
   [`research/README.md`](./research/README.md) for the frontmatter schema.
4. **Commit your note:**
   ```bash
   git add research/my-topic.md
   git commit -m "Add research note: my topic"
   ```
5. **Open a pull request.** A CI check validates your note's frontmatter and structure. A
   working-group tech lead will give it a quick look and merge.

## Filename convention

- Lowercase **kebab-case**, ending in `.md`: `research/agent-frameworks.md`.
- If your topic collides with an existing note, add your GitHub handle as a suffix:
  `research/agent-frameworks-rkoster.md`.

## Frontmatter

Every note starts with a YAML frontmatter block. Required keys: `title`, `author`, `date`,
`tags`, `status`, `sources`. The `cf_areas` key is optional. The full schema and field
descriptions live in [`research/README.md`](./research/README.md).

Tagging well matters — tags are how the workshop clusters notes into themes. See the
suggested (non-binding) vocabulary in
[`IDEATION.md`](./IDEATION.md#tagging-how-themes-will-emerge).

## Review & merge

Research notes are low-risk, so we optimize for throughput:

- CI validates frontmatter, filename, and required sections.
- Any working-group **tech lead** can merge once CI passes and the note is on-topic and not
  a duplicate.
- Substantive review of *ideas* happens at the workshop, not as a merge gate.

## Contributor License Agreement (CLA)

All committers to a Cloud Foundry Foundation project must sign a Contributor License
Agreement. You don't need to do anything up front: the **EasyCLA** bot comments on your
first pull request with a link to sign (individual or corporate). Once it's signed, the
CLA check goes green and your PR can be merged. You can also
[sign in to EasyCLA](https://corporate.v1.easycla.lfx.linuxfoundation.org/) ahead of time.

## Code of conduct

This project follows the [Cloud Foundry Code of Conduct](./CODE_OF_CONDUCT.md).
