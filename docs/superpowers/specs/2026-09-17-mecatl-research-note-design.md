# Mecatl Research Note Design

## Goal

Address issue #53 with a sourced research note on Mecatl as a cloud-native agent harness for
production workloads on infrastructure operators control.

## Scope

The note will cover Mecatl's streaming agent loop, provider-agnostic model integration, tools
and skills, permissions, hooks, delegation, durable sessions, append-only event logs, client
APIs, and the Kubernetes-native `mecak8s` runtime. It will discuss deny-dominant authorization,
derived delegated capabilities, attribution, audit, Redis-backed state, session leases, drain
handling, and disposable replicas.

The Cloud Foundry analysis will map Mecatl to CAPI-managed applications, Diego process
replacement and draining, UAA identity, service bindings for model/state stores, and
Loggregator audit/event streams. It will not claim existing Mecatl/CF integration.

## Structure and evidence

Create `research/mecatl.md` with the required four sections and frontmatter. Use the Mecatl
repository, README, official documentation, and deployment/runtime guides. Distinguish the
generic embedded engine from the Kubernetes reference runtime and label CF conclusions as
analysis or open questions.

## Validation

Run Devbox validation and tests, inspect whitespace/staged files, commit the note and plan on
`research/mecatl`, push, and open a PR targeting `main` without unrelated artifacts.
