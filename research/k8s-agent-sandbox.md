---
title: "Kubernetes Agent Sandbox (k8s-sigs)"
author: Ruben Koster (@rkoster)
date: 2026-07-02
tags: [sandboxing-isolation, runtime-lifecycle, ecosystem-survey]
cf_areas: [diego, garden-runc]
status: draft
sources:
  - https://github.com/kubernetes-sigs/agent-sandbox
---

## Summary

A Kubernetes SIG project providing a native sandbox control plane for AI agents. It offers
stable identity, persistence, and warm pools for agent workloads running on Kubernetes
clusters. It represents the cloud-native community's answer to "how should container
orchestrators support AI agent execution?"

## Key findings

- **K8s-native CRDs**: Defines Kubernetes custom resources for agent sandboxes — declarative
  specification of agent execution environments.
- **Stable identity**: Each agent sandbox gets a persistent identity (analogous to StatefulSet
  pod identity) that survives restarts. Critical for agents that need consistent credentials
  and state references.
- **Warm pools**: Pre-provisioned sandbox instances ready for immediate use, eliminating
  cold-start latency. Pool size managed declaratively.
- **Persistence**: Sandbox state persists across executions. Agents can resume work without
  rebuilding context from scratch.
- **Control plane separation**: The sandbox control plane manages lifecycle independently
  from the workload orchestrator — sandboxes are managed resources, not just pods.

## CF relevance

The project shows how the cloud-native community is extending a general-purpose container
orchestrator with agent-specific primitives. Stable sandbox identity maps to workload
identity patterns (e.g., SPIFFE/SVIDs). Warm pools address the cold-start latency problem
that affects interactive agent workloads. The control-plane-separated architecture — a
sandbox controller alongside the scheduler — is one model for how a platform could add agent
lifecycle management without replacing its core scheduling layer.

## Open questions

- What is the warm pool implementation — pre-created pods, or paused containers?
- How does stable identity interact with horizontal scaling (multiple instances of the same
  agent)?
- What persistence backend does it use (PVCs, external stores)?
- How does the project handle multi-tenancy?
