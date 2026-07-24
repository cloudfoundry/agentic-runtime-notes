---
title: "KEDA — Kubernetes Event-Driven Autoscaling"
author: Ruben Koster (@rkoster)
date: 2026-07-02
tags: [autoscaling, runtime-lifecycle]
cf_areas: [diego]
status: draft
sources:
  - https://keda.sh/
  - https://github.com/kedacore/keda
---

## Summary

KEDA (Kubernetes Event-Driven Autoscaling) is a [CNCF graduated project](https://www.cncf.io/projects/keda/)
that adds event-driven and queue-depth-based autoscaling to Kubernetes, including true
scale-to-zero and scale-from-zero. It sits alongside the [Kubernetes HPA](https://kubernetes.io/docs/concepts/workloads/autoscaling/horizontal-pod-autoscale/),
extending it with external metric sources rather than replacing it. KEDA is the de facto
standard for event-driven scaling on Kubernetes and ships [70+ scalers](https://keda.sh/docs/latest/scalers/)
([source](https://github.com/kedacore/keda/tree/main/pkg/scalers)) for common messaging
and queuing systems.

## Key findings

- **Three-component architecture**: KEDA Operator (watches ScaledObject CRDs and drives
  scaling decisions), Metrics Server (feeds external metrics to the Kubernetes HPA), and
  Scalers (connectors to event sources that pull metric data). Admission webhooks validate
  ScaledObject configurations at admission time.
- **Two CRDs for two workload shapes**: `ScaledObject` targets long-running
  Deployments/StatefulSets and manages replica count continuously. `ScaledJob` targets
  batch workloads — it creates Kubernetes Jobs on demand and cleans them up on completion,
  avoiding the problem of long-running workers accumulating in a `Terminating` state.
- **Activation vs. scaling thresholds**: KEDA separates the threshold for waking a
  scaled-to-zero workload (`activationThreshold`) from the threshold that drives ongoing
  scaling (`threshold`). This prevents false-wake oscillation on low-volume queues.
- **Scaler catalog**: 70+ built-in scalers covering RabbitMQ, Kafka, Redis (Lists and
  Streams), NATS JetStream, Temporal, Prometheus custom metrics, and cron schedules.
  TriggerAuthentication CRDs handle credential management for event source access,
  supporting cloud IAM, Kubernetes secrets, and Vault.
- **Pausing and forced activation**: Individual ScaledObjects can be paused (freeze
  at current replicas, scale to zero, or block scale-in/out independently) and
  force-activated (bypass the activation threshold to immediately scale from zero). This
  gives operators fine-grained control beyond simple min/max bounds.
- **Long-running execution handling**: KEDA provides two patterns for workloads that
  must not be interrupted mid-task: container lifecycle hooks that delay termination on
  SIGTERM until the current batch completes, and ScaledJob which models each task as a
  Job that runs to completion and exits cleanly.

## CF relevance

KEDA shows a mature, production-proven approach to the autoscaling problem that
HTTP-biased platforms have not needed to solve. The key gap it addresses — scale
workloads to zero when a queue is empty and wake them when messages arrive — is directly
relevant to agent workloads where tasks are discrete, arrival is unpredictable, and idle
compute is waste. The ScaledJob pattern is particularly relevant for agent sandboxes: each
tool invocation or sub-task could be modelled as a job that runs to completion rather than
a long-lived process waiting for work.

## Open questions

- KEDA operates at cluster scope; a multi-tenant platform would need space-scoped scaling
  boundaries — how would that work without a per-space KEDA operator?
- TriggerAuthentication maps naturally to service bindings — but does it support
  SPIFFE/SVID-based workload identity as a credential source, or only static secrets and
  cloud IAM?
- For agent workloads that hold expensive state in memory (loaded models, cached context),
  scale-to-zero means losing that state — how do KEDA users handle warm pools or
  pre-warming to amortize cold-start cost?
