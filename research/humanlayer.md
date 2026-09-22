---
title: "HumanLayer: Externalized Agent Sessions and Disposable Execution"
author: Ruben Koster (@rkoster)
date: 2026-09-18
tags: [durable-execution, orchestration, observability-governance, ecosystem-survey]
cf_areas: [capi, diego, loggregator]
status: draft
ratings:
  platform-impact:
    value: 84
    note: "HumanLayer illustrates a control plane where agent collaboration state is externalized while execution hosts remain replaceable."
  maturity:
    value: 62
    note: "The current product has local and remote daemons, multi-client collaboration, and documented persistence behavior, while the public architecture does not establish live process migration."
  novelty:
    value: 78
    note: "The combination of multiplayer task/artifact collaboration, full session visibility, remote daemons, and host-independent control is a distinctive platform pattern."
  actionability:
    value: 80
    note: "The architecture gives CF concrete questions about durable sessions, disposable processes, worktrees, identity, event streams, and host-bound capabilities."
sources:
  - https://github.com/humanlayer/humanlayer
  - https://humanlayer.com
  - https://docs.humanlayer.com/guide/remote-daemons
  - https://docs.humanlayer.com/explanation/remote-daemons
---

## Summary

HumanLayer is a multiplayer coding-agent workspace and cloud control plane that brings agent
sessions, plans, artifacts, worktrees, and code diffs together for teams. Its API coordinates
local or remote daemons, while daemons launch the actual coding-agent sessions on hosts with
the required code, tools, credentials, and private-network access. This supports a thesis of
agents becoming stateless at the process layer: collaboration and session events live outside
the process, while the daemon or process can be restarted or replaced, although public docs do
not establish migration of a live in-memory process between arbitrary containers.

## Key findings

- **HumanLayer separates control plane from execution host.** Web, desktop, and mobile clients
  request work through an API. A connected local or remote daemon receives the work, launches
  Claude or Codex sessions, and sends session events back through the API to each interface.
- **Tasks group the durable collaboration surface.** Tasks group sessions, artifacts, plans,
  designs, diffs, and worktrees so multiple humans and agents can collaborate on one unit of
  work. This external object model is more durable and shareable than the memory of a single
  agent process.
- **The product exposes full session visibility.** The website describes visibility into
  thinking messages, subagent tool calls, code changes, and real-time topology across daemons
  and clients. The event stream gives clients a way to reconnect to ongoing work without being
  attached to the agent process's terminal.
- **Remote daemons move execution, not necessarily process memory.** A remote daemon can run on
  a cloud VM, workstation, or private-network machine while the user controls sessions through
  the browser. The host provides access to code, tools, credentials, and private services. The
  public architecture supports dispatch and event streaming through the API, but does not prove
  that a live Claude/Codex process can be serialized and resumed in a different container.
- **Execution context remains host-bound.** Worktrees, filesystem state, installed tools,
  private network routes, credentials, and agent processes belong to the daemon host. Moving or
  replacing a process therefore requires either preserving that host context or reconstructing
  it from external state and repository history.
- **Authentication persistence is explicit.** Interactive login stores a session under
  `~/.humanlayer/riptide/`, and the daemon can reuse it after restart or host reboot if the same
  user and directory remain intact. Containers require persistent storage for those credentials;
  removing and recreating the container loses them unless the storage is mounted.
- **The statelessness thesis is layered.** HumanLayer externalizes task metadata, artifacts,
  plans, diffs, session events, and control-plane access. It does not imply that prompts,
  in-memory model context, shell state, process trees, or credentials are automatically portable
  across hosts. The practical model is stateless or replaceable orchestration around a potentially
  stateful execution environment.
- **Git is the change-transfer boundary.** The public product centers code diffs and worktrees,
  while the open repository documents that the older public code is largely deprecated and points
  to the current product. Git history and artifacts can make work portable even when the original
  runtime host cannot be reproduced exactly.
- **HumanLayer is multi-user by design.** Teammates can observe and interact with sessions from
  different interfaces, comment on artifacts, and send work to agents. That requires identity,
  access control, event fan-out, and protection for sensitive session content.

## CF relevance

HumanLayer provides a useful reference architecture for Cloud Foundry agents that should not
depend on one long-lived Diego process. CAPI could own tasks and session metadata, while Diego
hosts disposable agent processes whose durable state is stored externally. A replacement process
could rehydrate a task from conversation/event history, repository/worktree state, plans, and
artifacts rather than requiring the original process memory to survive.

The difficult boundary is completeness of rehydration. CF would need durable session and event
stores, stable workspace or worktree storage, identity and credential reissuance, session
ownership/fencing, and a way to reconstruct tool and private-network access. Loggregator could
stream process, tool, session, and collaboration events, but a durable control-plane history
would still be needed for reconnecting clients and recovering work after process replacement.

This model could reduce the need for stateful, permanently running agent containers while
preserving a rich interactive experience. It does not eliminate state; it moves state into
platform-managed records, repositories, artifacts, durable stores, and host capability
descriptions. The platform must decide which state is authoritative and how much execution
context is reproducible before claiming an agent is portable across Diego instances.

## Open questions

- Which parts of an agent session must be externalized for safe rehydration: conversation,
  model context, tool state, shell state, worktree, environment, artifacts, or all of them?
- Can a CF agent process be replaced during a turn, or only between explicit event boundaries?
- How should CAPI and Diego coordinate session ownership, fencing, draining, and recovery to avoid
  two processes acting on one task simultaneously?
- How should worktrees, uncommitted files, installed dependencies, credentials, and private
  network access be reconstructed on a replacement instance?
- Which user, agent, task, and daemon identities should authorize session access and tool calls?
- What event ordering, replay, retention, and privacy guarantees should Loggregator and the
  durable control plane provide?
- When does externalized state become sufficiently complete that process migration is practical,
  and when is it more honest to treat a new process as a continuation with a reconstructed
  context?
