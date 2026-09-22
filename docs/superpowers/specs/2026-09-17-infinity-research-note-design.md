# Reactive Agents Research Note Design

## Goal

Add a sourced comparative research note on Hydro Project's Infinity runtime and Reactive
Agent Protocol (RAP), MCP Tasks, and the experimental MCP Triggers & Events work, with an
architecture-first assessment of relevance to Cloud Foundry.

## Scope

The note will describe documented behavior from each upstream project, then clearly separate
Cloud Foundry analysis from upstream facts. It will cover:

- Infinity as a Rust agent runtime and reference implementation of RAP.
- Execution slices, durable conversation/state reconstruction, message-driven wake-ups,
  tool dispatch, callbacks, subscriptions, hibernation, and per-thread ordering.
- RAP's asynchronous tool contract and its relationship to synchronous MCP tools.
- Infinity's MCP compatibility layer and serverless deployment model.
- MCP Tasks as an official MCP extension with durable task state, receiver-generated task
  IDs, polling, and deferred result retrieval; identify the `2026-07-28` schema as stable
  according to its repository.
- MCP Triggers & Events as an explicitly experimental working group exploring proactive
  server notifications, polling, streams, webhooks, subscription TTLs, cursors/replay,
  signatures, delivery semantics, and ordering guarantees.
- The semantic differences and possible overlap between task lifecycles, event
  subscriptions, and reactive agent execution.
- Cloud Foundry relevance across Diego process lifecycle, CAPI-managed applications,
  external queues and state stores, scale-to-zero, and Loggregator observability.
- Open questions about convergence versus fragmentation, polling versus push/webhooks,
  callback authentication, delivery guarantees, ordering and deduplication, replay/cursors,
  state-store integration, cost semantics, and independent protocol adoption.

## Structure

Create `research/infinity.md` using the repository template and required sections:

1. Summary
2. Key findings
3. CF relevance
4. Open questions

The frontmatter will include the author, current date, relevant tags, `status: draft`,
primary Infinity/RAP and MCP extension sources, and provisional ratings with concise
justifications.

## Sources and evidence

Use the Infinity GitHub repository and README, runtime overview, runtime architecture,
Reactive Agent Protocol overview, RAP specification overview, and Lambda deployment
documentation. Also use the MCP Tasks repository and README, plus the MCP Triggers & Events
repository, README, and draft design sketch. The note will identify MCP Tasks as an official
extension repository, Triggers & Events as experimental, and will not describe RAP as an AAIF
or generally ratified standard unless an authoritative source establishes that status. Cloud
Foundry claims will be framed as analysis or open questions rather than presented as existing
integration.

## Validation

Run the repository's configured note validation and test script. Confirm that the new file
has valid frontmatter, a kebab-case filename, all required sections, linked sources, no
template placeholders, and only the intended tracked changes are committed and pushed in a
new PR.
