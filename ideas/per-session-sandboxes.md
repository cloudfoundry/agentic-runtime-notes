---
title: Per-session sandboxes with lifecycle states
author: Ruben Koster (@rkoster)
date: 2026-07-02
tags: [runtime-lifecycle, sandboxing-isolation]
---

## The idea

An agent app (the "harness") manages a pool of sandboxes scoped to a user session.
Each sandbox runs an isolated workload — a tool, a sub-task, a code execution — and
transitions through a set of lifecycle states: running (CPU + attached volume), suspended
(disk retained, CPU released), and dehydrated (no compute, state serialized to blobstore).
The harness decides which sandboxes are active and when to suspend or dehydrate them.

![Illustration: harness app with LLM service binding dispatching tool calls to per-session
sandboxes in running, suspended, and dehydrated states](./illustration-harness-sandboxes.svg)

## Why it might matter

Agent workloads are bursty and multi-step. A single user session may need several
concurrent sandboxes (parallel tool calls), but most of them are idle most of the time.
A platform that only supports "running" or "stopped" forces a choice between paying for
idle compute or losing state on every stop. Graduated lifecycle states let the platform
recover compute from idle sandboxes without discarding their work.

## What to research next

- How do existing sandbox platforms (Daytona, K8s Agent Sandbox) implement
  suspend/resume — memory snapshot vs. filesystem checkpoint?
- What is the right storage primitive for the dehydrated state — a volume snapshot,
  a tarball in blobstore, or a full container image layer?
- Does CF's existing volume service and blobstore give enough primitives to implement
  this, or are new platform APIs needed?

## Related

- [research/k8s-agent-sandbox.md](../research/k8s-agent-sandbox.md) — K8s-native sandbox
  control plane with warm pools and PVC-backed persistence; gVisor pod snapshots on GKE.
