---
title: Split environment staging from workspace state for agent sandboxes
author: Ruben Koster (@rkoster)
date: 2026-08-24
tags: [runtime-lifecycle, sandboxing-isolation, ecosystem-survey]
ratings:
  platform-impact:
    value: 84
    note: 'Initial review of Split environment staging from workspace state for agent sandboxes: its subject and tags indicate how broadly the capability could affect an agentic platform.'
  maturity:
    value: 46
    note: 'Initial review of Split environment staging from workspace state for agent sandboxes: this score reflects the amount of established external practice visible in the note.'
  novelty:
    value: 72
    note: 'Initial review of Split environment staging from workspace state for agent sandboxes: this score reflects how distinct or emerging the approach appears in the current landscape.'
  actionability:
    value: 76
    note: 'Initial review of Split environment staging from workspace state for agent sandboxes: this score reflects how readily the material could guide a focused experiment or follow-up.'

---

## The idea

Heroku's code-execution sandbox (see `research/heroku-ai-platform.md`) resolves an agent's
requested dependencies live: a `code_exec_python` tool call creates a fresh venv inside a
one-off dyno and runs `pip install <packages>` against the public PyPI index at request
time, then discards the venv. This assumes always-on internet egress to a public package
index at execution time — a poor fit for enterprises that run CF with offline/mirrored
buildpacks — and it's wasteful (repeated installs, no reuse across calls).

Working through this, two things an agent sandbox produces turned out to need very
different treatment, not one combined "install-then-run" step:

- **Environment** — the interpreter plus resolved library dependencies. This is expensive
  (network fetch, native-extension builds) and *shared*: many unrelated task executions
  with the same dependency manifest can reuse the same result. This is exactly what CF
  staging already does — a Build takes a manifest + buildpack + stack and produces an
  immutable, cacheable **Droplet**. No new capability needed here.
- **Workspace** — the agent's actual code/data for this turn. It isn't built, it's mounted:
  a Task is created from an environment Droplet (read-only base) with a workspace
  **Package** attached (mutable overlay) — image + volume, not two build stages. Turn-to-
  turn continuity is just uploading the workspace *diff* to blobstore, the same
  resource-matching mechanism `cf push` already uses to avoid re-uploading unchanged files.

A Task, then, composes two independently-cacheable references at creation time: an
environment Droplet (looked up/built by manifest hash) and a workspace Package (latest
blob manifest). Checkpointing an agent's sandbox state is a workspace diff-upload, not a
Droplet rebuild; resuming is creating a fresh Task from the same two references — there's
no in-process state to restore, only filesystem state, and filesystem state already
survives in blobstore by construction.

For the environment Droplet cache to pay off at platform scale, it should behave like a
Nix derivation rather than a per-app build artifact: the cache key is a pure hash of the
build inputs (buildpack version, stack, manifest content) — not the app, org, or space
that requested it. Many unrelated sandboxes across the whole platform asking for "Python
3.12 + numpy" should all resolve to the *same* Droplet, built once, the first time anyone
asks for that exact input set, and substituted (not rebuilt) for everyone after. This is a
different reuse scope than CF's current Droplet model, where a Droplet belongs to one app:
here the cache is global and content-addressed, closer to a Nix binary cache/substituter
sitting in front of Build than to an app's own droplet history. A small set of common
base environments ("latest Python + basic libs") could even be pre-warmed platform-wide so
most sandbox requests never trigger a Build at all — they hit the substituter immediately.

This also keeps the harness (the agent's reasoning loop) fully decoupled from the sandbox,
consistent with a "remote hands" model: the harness never runs inside or attaches to a
sandbox directly. It only ever calls out to two platform-side capabilities — resolve/build
an environment, and run a Task against a workspace — and the sandbox itself has no
identity or lifecycle beyond one Task execution. Mechanically this could be an MCP server
that's a thin wrapper over existing (or lightly extended) CAPI v3 resources:

- `get_or_build_environment(manifest) -> droplet_ref` — Build/Droplet, cached by manifest hash
- `upload_workspace_diff(workspace_ref, files) -> package_ref` — Package + existing bits/resource-matching
- `run_task(droplet_ref, package_ref, command) -> result` — Task, mounting both

## Same primitives, different composition

An ordinary CF app and an agent sandbox end up using exactly the same four primitives —
Package, Build, Droplet, Task — but bind them at different points and for different
reasons. Nothing here requires a new primitive; what differs is *what goes into the
Package*, *what the Droplet ends up containing*, and *what "reuse" means*.

| | Ordinary app | Agent sandbox |
|---|---|---|
| **Package contents** | The app's own source — relatively stable, changes per deploy | The agent's per-turn workspace — volatile, changes on nearly every invocation |
| **What the Droplet contains** | Environment *and* code, fused together immutably — any code change requires a new Build | Environment *only* — code is deliberately excluded from the Droplet, because it isn't known until the agent generates it |
| **Build trigger** | Deliberate, human/CI-initiated, roughly once per deploy | Implicit, content-addressed cache-fill — the first request for a given dependency-manifest hash stages it, every later request with the same hash reuses it |
| **Reuse axis** | One Droplet, many replicas of the *same* code (horizontal scaling) | One Droplet (environment), many *different* workspaces mounted against it (different code per Task) |
| **Execution primitive** | Long-running Process — routed, health-checked, restarted on crash | One-off Task — no routing, no restart; a failed Task is just reported back to the harness |
| **Identity/lifecycle** | Persistent — the app and its Droplet history outlive any single deploy | None beyond a single Task's run — the only thing that persists across turns is the workspace Package sitting in blobstore |

The pivotal difference is *where the line between Droplet and code falls*. For an app,
staging deliberately fuses code and environment into one immutable artifact, because the
whole point is to run many identical replicas of that exact code. For a sandbox, fusing
them would defeat the purpose: the code isn't known ahead of time (an LLM writes it per
turn), so baking it into the Droplet would force a full rebuild on every single
invocation — exactly the live-`pip install`-per-call problem this idea starts from. Moving
the code out of the Droplet and into a separately-mounted Package is what lets the
(expensive) environment be built once and the (cheap, volatile) code be swapped in per
Task without ever re-staging.

## Why it might matter

- Solves the original problem (live `pip install` per call, no offline path) using the
  existing Build→Droplet staging pipeline unmodified — no new dependency-resolution
  mechanism needed.
- Turns "durable execution" from a new primitive into a non-problem: continuity is just
  preserved workspace files in blobstore; there's nothing else to checkpoint or replay.
- Minimizes data movement on the hot path: the large, expensive environment is resolved
  once and reused; only the small per-turn workspace diff moves.
- Keeps the harness fully decoupled from the sandbox: the sandbox is just a Task, with no
  lifecycle or identity beyond a single run.
- Global, input-hashed caching means the *first* sandbox anywhere on the platform to ask
  for a given environment pays the build cost, and every other sandbox — any org, any
  space, any app — just substitutes the cached result, the same way a Nix binary cache
  turns "build a derivation" into "fetch a pre-built store path" for anyone who isn't first.

## What to research next

- Does CAPI v3 support the same Droplet being reused across many concurrently-created
  Tasks (potentially across apps/spaces) keyed by a manifest hash, or does today's model
  assume a Droplet belongs to exactly one app? What would shared-Droplet lookup require?
- A global, cross-tenant Droplet cache only holds for *pure* inputs — a manifest that only
  references public packages from a public index. The moment a manifest pulls from a
  private git repo, an internal package registry, or embeds a credential, the resulting
  Droplet can't be safely shared platform-wide and must fall back to tenant-scoped caching
  (same distinction Nix draws between fixed-output/pure derivations and impure ones). How
  would the platform detect or declare that boundary, and does it need to be explicit in
  the manifest (e.g. an allowlist of public index sources) rather than inferred?
- What's the right authority/trust model for a shared platform-wide cache — does every
  foundation/tenant trust the same set of upstream package indices and buildpack versions,
  or does global sharing need to be scoped to some smaller trust boundary (e.g. per
  foundation) rather than truly platform-global?
- Is there an existing CF/Diego mechanism for mounting an extra read-write volume (the
  workspace Package) alongside a Droplet's read-only rootfs at Task creation, or would this
  need new Garden/Diego plumbing?
- What's the natural boundary for a workspace Package — one Package per agent session,
  updated turn over turn, or a new immutable Package per turn (cheap due to
  resource-matching dedup, and gives free history/rollback for free)?
- Explicitly out of scope: in-process/in-memory continuity (e.g. a long-lived REPL kept
  warm across turns). This model only preserves filesystem state between Task executions —
  is that sufficient for the working group's agent use cases, or does some class of agent
  need warm-process continuity too?
- Would `get_or_build_environment` / `upload_workspace_diff` / `run_task` as MCP tools be a
  wrapper purely over existing CAPI v3 endpoints (Build, Package bits/resource-match, Task),
  or does it need genuinely new CAPI capability?
- This may simplify `per-session-sandboxes.md`'s three-state lifecycle (running/suspended/
  dehydrated) down to two effective states — an active Task, or nothing, since workspace
  state is already durably externalized by default. Does "suspended" (CPU released, disk
  retained) still have a distinct use case once the workspace is always resting in
  blobstore, or does it collapse into "dehydrated"?

## Related

- [research/heroku-ai-platform.md](../research/heroku-ai-platform.md) — Heroku's code
  execution sandbox: dependencies are resolved live per-call via `pip install` in a
  throwaway venv inside a one-off dyno, with no documented offline/caching path.
- [ideas/per-session-sandboxes.md](./per-session-sandboxes.md) — lifecycle states
  (running/suspended/dehydrated) for sandboxes; see the open question above on whether
  this idea's environment/workspace split changes which of those states are still useful.
- [research/anthropic-managed-agents.md](../research/anthropic-managed-agents.md) —
  provision/execute split for on-demand tool sandboxes; a comparison point for whether
  "provision" there is closer to a cached environment or to Heroku's live-install model.
