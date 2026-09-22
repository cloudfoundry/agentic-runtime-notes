---
title: "Docker Sandboxes: Local MicroVMs for Coding Agents"
author: Ruben Koster (@rkoster)
date: 2026-09-19
tags: [sandboxing-isolation, runtime-lifecycle, identity, ecosystem-survey]
cf_areas: [diego, capi, uaa, loggregator]
status: draft
ratings:
  platform-impact:
    value: 68
    note: "Docker Sandboxes demonstrates strong isolation and policy boundaries for coding agents, but its documented execution model is developer-local rather than a shared Cloud Foundry service."
  maturity:
    value: 72
    note: "Docker documents a dedicated CLI, microVM architecture, workspace modes, network policy, credential handling, and optional organization governance."
  novelty:
    value: 55
    note: "MicroVM isolation and nested Docker are established patterns; the product packages them around coding-agent workflows, local workspaces, and policy enforcement."
  actionability:
    value: 48
    note: "The documented local-first CLI is useful prior art, but it does not establish a remotely consumable lifecycle-and-execution API for multi-tenant CF workloads."
sources:
  - https://www.docker.com/products/docker-sandboxes/
  - https://docs.docker.com/ai/sandboxes/
  - https://docs.docker.com/ai/sandboxes/architecture/
  - https://github.com/opensandbox-group/OpenSandbox
---

## Summary

Docker Sandboxes is local-first developer tooling: the `sbx` CLI runs a supported coding-agent
harness inside a dedicated microVM on the developer's machine. It is more than putting a harness
in a container because each sandbox owns a Docker daemon, filesystem, and network, but Docker's
sandbox and execute all actions in it. OpenSandbox is the closer prior-art match for that latter
model because it publishes lifecycle, command-execution, and file-operation APIs through SDKs and
MCP, with Docker and Kubernetes runtimes.

## Key findings

- **`sbx` starts the agent locally.** `sbx run <agent>` creates a sandbox and launches a
  supported coding agent in it. The documented workflow begins in a local project directory and
  is designed to give that local agent unattended execution without modifying the host directly.
- **The isolation boundary is a microVM, not just a container.** Each sandbox has its own
  filesystem, network, and Docker daemon, so an agent can install packages and build or run
  containers without receiving the host Docker daemon or host filesystem by default. Docker
  explicitly contrasts this with a container that mounts the host socket or privileged
  Docker-in-Docker.
- **Workspace choice controls where changes land.** A directly mounted workspace exposes the
  developer's project through a filesystem passthrough; mountless sandboxes retain files inside
  the sandbox; and clone mode mounts the host source read-only while the agent works in a private
  clone. These are local development and review choices, not a remote artifact API.
- **Network and credentials are mediated by host-side components.** All outbound TCP traffic is
  routed through a proxy on the host. The HTTP/HTTPS path can enforce network policy and inject
  credentials, avoiding a need to expose real credentials directly to the agent process.
- **MCP policy also stays on the host side.** The MCP gateway brokers access to registered MCP
  servers and applies MCP policy before tool, resource, prompt, or gateway meta-tool operations.
  A registered server may itself be remote, but that does not make the sandbox lifecycle or shell
  execution remote.
- **Central governance distributes policy, not a shared sandbox service.** Docker documents
  optional paid organization governance for centrally managed network, filesystem, and MCP
  policies across developer machines. The published model remains a local `sbx` environment;
  it does not document a platform endpoint that another agent harness can use for sandbox create,
  exec, inspect, file, and destroy operations.
- **OpenSandbox represents a different boundary.** OpenSandbox publishes sandbox lifecycle and
  execution APIs, language SDKs, a CLI, and an MCP server for sandbox creation, command execution,
  and file operations. Its Docker and Kubernetes runtimes, ingress and egress controls, and
  credential vault make it closer to a remotely programmable sandbox substrate than Docker
  Sandboxes' local agent environment.

## CF relevance

Docker Sandboxes offers useful prior art for a Cloud Foundry agent-sandbox design: a hard
execution boundary, a separate Docker daemon, workspace isolation modes, mediated egress, proxy
credential injection, and policy enforcement at MCP boundaries. Those capabilities could inform a
CF service that protects the platform host and makes sandbox activity observable through platform
logging and audit facilities.

It does not, based on its published documentation, provide the remote execution control plane a
Cloud Foundry platform integration needs. An `execd`-style substrate must let a separate agent
harness create a sandbox, execute commands, transfer or inspect files, observe lifecycle state,
and destroy the sandbox through an authenticated API. It also needs platform tenancy, lifecycle,
quota, route, identity, and audit integration. OpenSandbox's published lifecycle and execution
APIs are closer prior art for this remote boundary, while Docker Sandboxes is stronger evidence
for the local developer experience and isolation model.

## Open questions

- Will Docker expose a remotely consumable lifecycle and execution API, or remain focused on
  developer-local `sbx` workflows?
- Can the microVM, egress proxy, credential injection, and MCP gateway operate independently of
  Docker Desktop and a developer workstation?
- Does organization governance emit auditable policy and execution events that an external
  platform control plane could consume?
- Which workspace model would be appropriate for a CF-hosted agent that must retain work without
  exposing application source or artifacts across tenant boundaries?
