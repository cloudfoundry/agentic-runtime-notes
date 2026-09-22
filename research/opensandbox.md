---
title: "OpenSandbox: Universal Sandbox Infrastructure for AI Applications"
author: Ruben Koster (@rkoster)
date: 2026-09-17
tags: [sandboxing, workload-isolation, orchestration, ecosystem-survey]
cf_areas: [capi, diego]
status: draft
ratings:
  platform-impact:
    value: 87
    note: "OpenSandbox targets the isolation, lifecycle, networking, and credential problems that arise when platforms run many untrusted AI workloads."
  maturity:
    value: 68
    note: "The project has standardized APIs, multiple SDKs, Docker/Kubernetes runtimes, MCP integration, and security guides, but operational maturity still needs evaluation."
  novelty:
    value: 74
    note: "Its combination of a portable sandbox protocol, AI-specific environments, per-sandbox egress, credential vault, and multiple isolation backends is distinctive."
  actionability:
    value: 84
    note: "The lifecycle and execution API boundaries provide concrete comparison points for Diego and a CF-adjacent secure-agent substrate."
sources:
  - https://open-sandbox.ai/
  - https://github.com/opensandbox-group/OpenSandbox
  - https://raw.githubusercontent.com/opensandbox-group/OpenSandbox/main/README.md
  - https://github.com/opensandbox-group/OpenSandbox/tree/main/specs
  - https://github.com/opensandbox-group/OpenSandbox/tree/main/docs/architecture
  - https://github.com/opensandbox-group/OpenSandbox/blob/main/docs/guides/credential-vault.md
  - https://github.com/opensandbox-group/OpenSandbox/blob/main/docs/guides/secure-container.md
---

## Summary

OpenSandbox is general-purpose sandbox infrastructure for AI applications, with standardized
lifecycle and execution APIs, multi-language SDKs, CLI and MCP interfaces, and Docker and
Kubernetes runtimes. It provides command, filesystem, and code-interpreter environments for
coding agents, browser automation, remote development, and model-generated code. Its per-sandbox
network controls, credential vault, and gVisor/Kata/Firecracker options make it a useful
reference for a secure-agent execution substrate adjacent to Cloud Foundry.

## Key findings

- **The project separates protocol from runtime.** OpenSandbox defines sandbox lifecycle and
  execution APIs so custom runtimes can implement a common interface. The built-in runtimes
  support local Docker and distributed Kubernetes deployment, but the API boundary is intended
  to be portable.
- **Lifecycle is a first-class API.** The platform supports provisioning, monitoring, renewing,
  pausing/resuming, and terminating sandbox instances. This gives clients a control surface for
  agent sessions rather than treating each command as an unmanaged container invocation.
- **Clients are available across languages and interfaces.** Python, Java/Kotlin,
  JavaScript/TypeScript, C#/.NET, and Go SDKs sit alongside the `osb` CLI and an MCP server.
  MCP clients can create sandboxes, execute commands, and perform file operations through the
  sandbox service.
- **The execution model covers multiple AI workloads.** Built-in environments include command,
  filesystem, and code interpreter capabilities. Examples target coding agents, browser
  automation with Chrome/Playwright, remote development with VS Code, desktop/VNC environments,
  and AI code execution.
- **Network policy is sandbox-scoped.** OpenSandbox provides a unified ingress gateway with
  routing strategies and per-sandbox egress controls. This is important for agents that need
  controlled access to package registries, model APIs, source repositories, and private
  services.
- **Credential injection avoids exposing raw secrets to workloads.** The credential vault is
  designed to inject credentials for outbound requests without exposing real secrets directly
  to the sandboxed workload. Rotation, scope, audit, and failure behavior remain platform
  responsibilities.
- **Isolation has multiple implementation choices.** The project supports ordinary containers
  and documents stronger isolation options including gVisor, Kata Containers, and Firecracker
  microVMs. The security boundary, startup cost, feature compatibility, and operational burden
  differ by backend.
- **MCP makes sandbox control available to agents.** The MCP server exposes lifecycle and
  execution operations to MCP-capable clients such as Claude Code and Cursor. This is powerful
  but creates a security boundary: an agent that can create sandboxes or run commands needs
  explicit authorization, quotas, and audit.
- **OpenSandbox is infrastructure, not an agent framework.** It runs commands, filesystems,
  browsers, and tools, but does not define an agent's model loop, memory, delegation policy, or
  business authorization. Those concerns can be layered above the sandbox APIs.
- **Distributed scheduling and state need explicit design.** Kubernetes enables large-scale
  scheduling, while pause/resume, files, ports, logs, metrics, and workspace state need clear
  persistence and recovery semantics when a sandbox is moved, restarted, or terminated.

## CF relevance

OpenSandbox provides a useful decomposition for Cloud Foundry's secure-agent story. Diego could
continue managing ordinary application processes, while a sandbox service handles workloads
that require stronger isolation, arbitrary packages, browsers, nested tooling, or model-generated
code execution. CAPI could manage sandbox-service instances and service bindings that expose
lifecycle endpoints, workspace storage, network policy, and credential references.

The protocol boundary could let CF integrate multiple backends without exposing their details to
agent clients. A Docker-backed implementation might serve development or lower-risk workloads,
while gVisor, Kata, or Firecracker handles untrusted multi-tenant execution. CF networking and
security groups would still need to coordinate with per-sandbox ingress/egress policy, and UAA
or workload identity would need to authorize creation, command execution, file access, and
credential use.

This likely belongs beside rather than entirely inside Diego. Diego provides process lifecycle,
placement, health, and desired state; a secure-agent substrate adds sandbox identity,
checkpoint/termination semantics, per-sandbox network identity, credential mediation, and
resource accounting. Loggregator-compatible events should correlate sandbox lifecycle, commands,
tool calls, egress decisions, credential use, and agent/session identity without logging
secrets or sensitive command contents by default.

## Open questions

- Should CF offer OpenSandbox as a brokered service, integrate its protocol into Diego, or build
  a smaller native sandbox substrate with compatible lifecycle boundaries?
- Which isolation backend is appropriate for each workload class, and how should CF expose the
  security and compatibility trade-offs to application teams?
- How should sandbox identity map to UAA users, CF applications, spaces, agent sessions, and
  delegated tools?
- How should sandbox files, workspace state, ports, logs, and paused sessions persist across
  worker replacement, quota changes, and termination?
- Which egress destinations and credential scopes should be allowed per sandbox, and how should
  vault injection, rotation, revocation, and auditing work?
- What quotas should govern sandbox count, CPU, memory, storage, network, command duration, and
  concurrent MCP operations?
- Which lifecycle, execution, policy, and security events should Loggregator expose, and which
  belong in a protected audit system?
