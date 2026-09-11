---
title: "wasmCloud — a WebAssembly-native alternative to Dapr's sidecar model"
author: Ruben Koster (@rkoster)
date: 2026-08-10
tags: [sandboxing-isolation, runtime-lifecycle, ecosystem-survey, orchestration]
cf_areas: []
status: draft
sources:
  - https://github.com/wasmCloud/wasmCloud
  - https://wasmcloud.com/
  - https://wasmcloud.com/docs/
  - https://wasmcloud.com/docs/v1/concepts/
  - https://www.cncf.io/projects/wasmcloud/
  - https://wasmcloud.com/blog/2025-01-15-running-distributed-ml-and-ai-workloads-with-wasmcloud
ratings:
  platform-impact:
    value: 48
    note: 'CF lacks deny-by-default WIT capability contracts, but its general container hosting already covers far more workloads; wasmCloud requires WASI components and is not a direct replacement for buildpack applications.'
  maturity:
    value: 65
    note: 'wasmCloud is a CNCF Incubating project with multi-organization maintainers, but its v1 architecture is no longer maintained and the early-2026 v2 Kubernetes rearchitecture leaves compatibility and operational questions.'
  novelty:
    value: 70
    note: 'Language-neutral WIT imports as enforceable deny-by-default capabilities and swappable in-process providers offer an unconventional alternative to container and sidecar security models.'
  actionability:
    value: 35
    note: 'The document flags capability security as inspiration but finds no clear CF mapping; WASI support for Python and Node agent dependencies, v2 clustering, and a representative MCP workload all need discovery first.'

---

## Summary

wasmCloud is a CNCF Incubating project that runs polyglot applications as WebAssembly (WASI)
components instead of containers, with pluggable "capability" backends (key-value, blob
storage, messaging, HTTP) conceptually similar to Dapr's building blocks. Where Dapr adds a
sidecar process next to your existing containerized app, wasmCloud requires compiling your
workload to a WASM component targeting WASI Preview 2 — a fundamentally different, and more
demanding, packaging model. The project has recently (early 2026) undergone a significant
rearchitecture ("v2") away from a NATS-only lattice toward a Kubernetes-native operator model.

## Key findings

- **Governance and license**: Apache-2.0. Accepted into CNCF on July 13, 2021; moved to
  **Incubating** on November 8, 2024 ([CNCF project page](https://www.cncf.io/projects/wasmcloud/)).
  Primary driving organization is **Cosmonic** (holds the CTO role and most maintainer seats
  across `wash`, Go tooling, and CI); other listed maintainers/contributing orgs include
  Capital One, Adobe, Synadia (the company behind NATS), Betty Blocks, T-Bank, and Helmet
  Security ([MAINTAINERS.md](https://github.com/wasmCloud/wasmCloud/blob/main/MAINTAINERS.md)).
- **Capability model, v1 (classic, "no longer actively maintained" per current docs)**:
  applications are built from **components** (stateless WASM logic) and **providers**
  (long-running host plugins implementing capabilities like key-value storage). These run on
  **hosts** (a Wasmtime runtime node) clustered into a **lattice** — a self-forming NATS mesh
  spanning cloud/on-prem/edge. Components and providers are joined via explicit **links**
  matching a component's imports to a provider's exports
  ([v1 concepts](https://wasmcloud.com/docs/v1/concepts/)). This is the architecture most
  existing wasmCloud writeups describe.
- **Capability model, v2 (current)**: the project has replaced the standalone-provider/lattice
  model with a **Kubernetes Operator** (`runtime-operator`) that reconciles CRDs (`Host`,
  `Workload`, `WorkloadDeployment`, `WorkloadReplicaSet`, `Artifact`) and schedules workloads
  onto host pods; routing runs through standard Kubernetes Services/EndpointSlices rather than
  a dedicated gateway (the `runtime-gateway` HTTP proxy is deprecated as of 2.0.3). Capabilities
  are now exposed through `wash-runtime`, an embeddable Rust runtime wrapping Wasmtime with a
  **plugin-based capability model**: built-in WASI (`wasi:filesystem`, `wasi:clocks`,
  `wasi:random`, `wasi:sockets`, `wasi:cli`), an HTTP ingress (`wasi:http`), and host plugins
  for `wasi:keyvalue`, `wasi:blobstore`, `wasi:config`, `wasi:logging`, and
  `wasmcloud:messaging` — pluggable, swappable backends, but now implemented as in-process
  runtime plugins rather than separate sidecar-like provider processes
  ([wasmCloud README](https://github.com/wasmCloud/wasmCloud)). Recent release notes (e.g.
  "2.4.0: HPA + KEDA autoscaling... pluggable NATS") suggest NATS itself has become an optional
  dependency rather than a hard requirement in v2 — worth verifying directly with a maintainer,
  as I did not read the full release notes to confirm scope.
- **Security posture — deny-by-default vs. containers' allow-by-default**: a WASM component can
  do nothing (no filesystem, network, or syscalls) unless it explicitly imports a WIT interface
  granting that capability; the runtime enforces this rather than it being bolted on with
  seccomp/AppArmor policies after the fact. Capabilities are declared *in the component itself*
  as language-agnostic interfaces, making the access surface visible and auditable
  ([wasmCloud docs, "Why wasmCloud?"](https://wasmcloud.com/docs/)).
- **Packaging and portability**: workloads are built with the `wash` CLI from any language that
  targets WASI Preview 2 (Rust, Go, TypeScript, Python, and — per a dedicated blog post — C),
  pushed/pulled as OCI artifacts (`wash oci`), and run identically across Linux, macOS, Windows,
  ARM, and x86 without a rebuild — a genuinely different portability story than multi-arch
  container images, which do require separate builds per architecture.
- **Performance claims**: wasmCloud's own marketing states "sub-millisecond start times" and
  "scale-to-zero with zero cold starts." These are vendor claims from the project's homepage,
  not independently verified in this research — worth treating as a hypothesis to validate
  rather than an established fact.
- **AI/agent workload evidence — hedged**: I found one substantive piece of content connecting
  wasmCloud to AI workloads: a January 2025 blog post by Cosmonic's CTO,
  ["Running distributed ML and AI workloads with wasmCloud"](https://wasmcloud.com/blog/2025-01-15-running-distributed-ml-and-ai-workloads-with-wasmcloud),
  covering `wasi-nn` and `wasi-webgpu` for edge inference, with a demo of an image-analyzer
  component and swappable ML capability providers. This is about **model inference at the
  edge**, not LLM-based autonomous agents specifically. I did not find dedicated agent-framework
  integrations, MCP support, or an agent-oriented sample in the
  [`examples/`](https://github.com/wasmCloud/wasmCloud/tree/main/examples) directory (which
  currently holds `blobby`, `grpc-hello-world`, `http-hello-world-persistent-storage`,
  `oci-registry`, `otel-config`, `qrcode`) or via a GitHub code/repo search scoped to the
  `wasmCloud` org. This search was not exhaustive (e.g. it doesn't cover wasmCon talks, Cosmonic's
  own blog, or community repos outside the org), so I'd phrase this as "no clear evidence found
  yet" rather than "wasmCloud is not used for agents."
- **Adoption cost vs. Dapr — the core architectural trade-off**: Dapr's sidecar model lets you
  keep an existing app, in its existing language runtime and container image, and add
  distributed-systems building blocks (state, pub/sub, service invocation) via a local HTTP/gRPC
  API exposed by `daprd` running alongside it — no recompilation. wasmCloud's component model
  requires compiling (or recompiling) your application to target WASI Preview 2 as a WASM
  component; existing containerized applications cannot be dropped in unchanged. Both offer a
  "pluggable backend" abstraction for common concerns, but the wasmCloud path is a genuinely
  different, higher-friction adoption cost tied to language/toolchain WASI support maturity,
  not just a deployment-time config change.

## CF relevance

Cloud Foundry today runs arbitrary compiled applications in containers via buildpacks — the
opposite starting point from wasmCloud, which only runs WASI-targeting WASM components. That
makes wasmCloud a poor drop-in replacement for CF's general-purpose app hosting, but its
deny-by-default capability model is an interesting reference point for the sandboxing/isolation
questions raised in `k8s-agent-sandbox.md` and `azure-hosted-agents.md` — particularly for
untrusted or third-party agent tool code, where "no capability unless declared" is a stronger
default than container-level network policies. The WIT-interface-as-capability-contract idea is
also a loose conceptual cousin of CF service bindings, though the mechanisms are unrelated. Not
sure yet whether this maps to anything concrete for CF's execution model — flagging the
connection rather than asserting one.

## Open questions

- Is NATS now truly optional in wasmCloud v2, or still a soft dependency for multi-host
  clustering? The release notes hint at "pluggable NATS" but I haven't confirmed the details.
- Given the WASI-targeting requirement, how mature is support for the languages/frameworks most
  agent tooling is actually written in today (Python with native-extension-heavy ML/agent
  libraries, Node.js agent SDKs)? The homepage lists Python as supported, but agent workloads
  often pull in dependencies (native code, dynamic imports) that may not compile cleanly to WASI
  Preview 2.
- Has anyone in the CNCF/Cosmonic ecosystem published a concrete LLM-agent-on-wasmCloud sample
  (e.g. an MCP tool server as a component) since the January 2025 ML/AI blog post? Worth asking
  at the workshop rather than assuming either way.
- How would wasmCloud's per-component capability model interact with an agent's need for dynamic,
  runtime-negotiated tool access (as opposed to statically declared interfaces at build time)?
