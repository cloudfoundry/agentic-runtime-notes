---
title: Decouple staging from execution for agent code-sandboxes
author: Ruben Koster (@rkoster)
date: 2026-08-24
tags: [runtime-lifecycle, sandboxing-isolation, ecosystem-survey]
---

## The idea

Heroku's code-execution sandbox (see `research/heroku-ai-platform.md`) resolves an agent's
requested dependencies live: a `code_exec_python` tool call creates a fresh venv inside a
one-off dyno and runs `pip install <packages>` against the public PyPI index at request
time, then discards the venv. This works, but it assumes always-on internet egress to a
public package index at execution time — a poor fit for enterprises that run CF with
offline/mirrored buildpacks and no direct-to-internet egress from app containers, and it's
wasteful (repeated installs, no reuse across calls).

CF/Heroku already has a primitive that solves an equivalent problem for ordinary apps:
staging. `cf push` separates "resolve dependencies and produce an immutable droplet" from
"run app instances from that droplet." Applying the same split to agent sandboxes suggests
two decoupled primitives instead of one combined "install-then-run" tool call:

- **Stage**: given a dependency manifest (e.g. a `requirements.txt` fragment, or a set of
  package specs), run it through the platform's existing (possibly offline/mirrored)
  buildpack pipeline to produce a cacheable, content-addressed droplet/image.
- **Execute**: given an already-staged environment reference, run a command/snippet in a
  fresh sandbox instance from that droplet — no network or dependency resolution needed at
  execution time.

Exposed as an MCP server, this could look like two tools — `stage_sandbox_environment(manifest) -> environment_ref`
and `exec_in_sandbox(environment_ref, code) -> result` — rather than one tool that does
both every time.

## Why it might matter

- **Offline/air-gapped compatibility**: staging can go through the same offline buildpack
  mirror/cache CF operators already run for ordinary app deploys; execution then needs no
  internet egress at all, matching typical enterprise network policy.
- **Reuse and cost**: if the environment is content-addressed by manifest hash, repeated
  invocations with the same dependency set reuse the same droplet instead of re-resolving
  and re-downloading every call — this is the actual lever for "reduce the amount of data
  moved around," since the platform (not the agent) decides when a droplet can be reused
  vs. rebuilt.
- **Right-sized primitives**: the goal isn't just "cache pip installs" — it's finding the
  abstraction boundary (environment vs. invocation) that lets the platform make caching,
  sharing, and locality decisions transparently, the same way droplets let Diego schedule
  app instances without re-staging on every restart.

## What to research next

- Could Diego's existing staging pipeline (staging container → droplet) be reused directly
  for sandbox environments, keyed by a hash of the dependency manifest, or does it need a
  lighter-weight variant for how often/quickly agent sandboxes are likely to request new
  environments?
- What's the right cache/eviction policy for staged environments — per-org, per-space, or
  shared across tenants (subject to isolation policy)?
- What's the right MCP tool granularity: separate `stage` and `exec` tools (explicit to the
  agent), or a single tool where staging is transparently cached behind the scenes and the
  agent never knows the difference?
- How does a "stage vs. execute" split interact with the lifecycle-state model in
  `per-session-sandboxes.md` (running/suspended/dehydrated) — is staging a zeroth phase
  before a sandbox is ever "running," or a distinct concept entirely?
- Does Anthropic's `provision({resources}) → execute(name, input)` split (see
  `research/anthropic-managed-agents.md`) already capture this, or is "provision" there
  closer to Heroku's live-install model (resources chosen at provision time, not a cached
  build artifact)?

## Related

- [research/heroku-ai-platform.md](../research/heroku-ai-platform.md) — Heroku's code
  execution sandbox: dependencies are resolved live per-call via `pip install` in a
  throwaway venv inside a one-off dyno, with no documented offline/caching path.
- [ideas/per-session-sandboxes.md](./per-session-sandboxes.md) — lifecycle states
  (running/suspended/dehydrated) for sandboxes; this idea adds a "staged, not yet running"
  phase ahead of that lifecycle.
- [research/anthropic-managed-agents.md](../research/anthropic-managed-agents.md) —
  provision/execute split for on-demand tool sandboxes.
