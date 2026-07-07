---
title: "Kubernetes Agent Sandbox (k8s-sigs)"
author: Ruben Koster (@rkoster)
date: 2026-07-02
tags: [sandboxing-isolation, runtime-lifecycle, ecosystem-survey]
cf_areas: [diego, garden-runc]
status: draft
sources:
  - https://github.com/kubernetes-sigs/agent-sandbox
  - https://agent-sandbox.sigs.k8s.io/docs
---

## Summary

A Kubernetes SIG project providing a native sandbox control plane for AI agents. It offers
stable identity, persistence, and warm pools for agent workloads running on Kubernetes
clusters. It represents the cloud-native community's answer to "how should container
orchestrators support AI agent execution?"

## Key findings

- **K8s-native CRDs**: Core `Sandbox` CRD plus three extensions — `SandboxTemplate`
  (reusable runtime config), `SandboxClaim` (user-facing allocation abstraction), and
  `SandboxWarmPool` (pre-warmed pools). Together these give a declarative API without
  hand-stitching StatefulSets, Services, and PVCs.
- **Stable identity — singleton model**: Each Sandbox has a stable hostname and network
  identity. Sandboxes are explicitly *singleton* (one pod per object), designed for
  workloads that don't fit the replicated model of Deployments or the numbered model of
  StatefulSets. Horizontal "scaling" means creating multiple independent Sandbox objects,
  each with its own identity — not replicas sharing one.
- **Warm pools — pre-created running pods**: `SandboxWarmPool` maintains a pool of fully
  provisioned, running pods ready to be claimed in milliseconds. Pods are pre-created and
  live (not paused or frozen), then adopted by a `SandboxClaim` on demand. Pool size is
  managed declaratively.
- **Persistence via PVCs**: Persistent storage uses standard Kubernetes
  `volumeClaimTemplates` — identical semantics to StatefulSet. Each Sandbox gets its own
  dynamically provisioned PVC backed by the cluster's StorageClass. GKE clusters running
  gVisor additionally support pod snapshots: full memory-state freeze to persistent storage
  for cost-efficient suspend/resume between agent turns.
- **Multi-tenancy via K8s primitives**: Standard K8s RBAC, namespaces, network policies,
  and resource quotas apply as usual. Isolation depth is a runtime choice: gVisor for
  kernel-level sandboxing, or Kata Containers for VM-grade isolation with a dedicated
  kernel per sandbox. The API is decoupled from the isolation mechanism.
- **Lifecycle management**: The controller handles creation, scheduled deletion,
  hibernation (pause to free compute), and automatic resume on incoming network activity —
  sandboxes are managed resources, not just pods.

## CF relevance

The project shows how the cloud-native community is extending a general-purpose container
orchestrator with agent-specific primitives. The singleton + stable-identity model contrasts
with the replicated-stateless model that most PaaS platforms optimize for. Warm pools
(pre-created pods assigned on claim) are a concrete answer to cold-start latency for
interactive agent workloads. The multi-tenancy model — standard K8s RBAC plus pluggable
runtime isolation — separates policy enforcement from isolation mechanism, treating isolation
depth as a deployment choice rather than a fixed platform guarantee.

## Open questions

- Can warm pool pods be pre-loaded with large model artifacts or dependency caches, or does
  storage provisioning happen separately from pod pre-warming?
- How does scheduling work on mixed-runtime clusters (some nodes with gVisor, others with
  Kata Containers) — is runtime selection per Sandbox spec or per namespace?
- What is the story for direct agent-to-agent communication across Sandboxes within a
  namespace — direct pod networking, or routed through a service?
