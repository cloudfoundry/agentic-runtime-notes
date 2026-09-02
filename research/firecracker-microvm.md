---
title: "Firecracker — Hardware-Isolated microVMs for Untrusted, Ephemeral Compute"
author: Ruben Koster (@rkoster)
date: 2026-08-10
tags: [sandboxing-isolation, runtime-lifecycle, ecosystem-survey]
cf_areas: []
status: draft
sources:
  - https://github.com/firecracker-microvm/firecracker
  - https://github.com/firecracker-microvm/firecracker/blob/main/docs/design.md
  - https://github.com/firecracker-microvm/firecracker/blob/main/CHARTER.md
  - https://github.com/firecracker-microvm/firecracker/blob/main/SPECIFICATION.md
  - https://github.com/firecracker-microvm/firecracker/blob/main/docs/snapshotting/snapshot-support.md
  - https://firecracker-microvm.github.io/
  - https://fly.io/blog/sandboxing-and-workload-isolation/
  - https://aws.amazon.com/blogs/aws/firecracker-lightweight-virtualization-for-serverless-computing
ratings:
  platform-impact:
    value: 70
    note: 'Initial review of Firecracker — Hardware-Isolated microVMs for Untrusted, Ephemeral Compute: its subject and tags indicate how broadly the capability could affect an agentic platform.'
  maturity:
    value: 76
    note: 'Initial review of Firecracker — Hardware-Isolated microVMs for Untrusted, Ephemeral Compute: this score reflects the amount of established external practice visible in the note.'
  novelty:
    value: 62
    note: 'Initial review of Firecracker — Hardware-Isolated microVMs for Untrusted, Ephemeral Compute: this score reflects how distinct or emerging the approach appears in the current landscape.'
  actionability:
    value: 66
    note: 'Initial review of Firecracker — Hardware-Isolated microVMs for Untrusted, Ephemeral Compute: this score reflects how readily the material could guide a focused experiment or follow-up.'

---

## Summary

Firecracker is an open-source Virtual Machine Monitor (VMM), written in Rust, that AWS built
and open-sourced in 2018 (Apache-2.0) to power AWS Lambda and Fargate's multi-tenant
serverless infrastructure. It creates "microVMs" — minimal, KVM-based virtual machines that
combine the strong isolation boundary of hardware virtualization with boot times and memory
overhead close to that of a container. Architecturally it is the deliberate opposite of QEMU:
rather than emulating a general-purpose PC (BIOS, legacy devices, broad OS compatibility),
Firecracker exposes only five devices and boots a pre-configured Linux kernel directly, cutting
both attack surface and startup latency. It sits at the "full hardware VM" end of the
container→microVM→full-VM isolation spectrum already touched on in `k8s-agent-sandbox.md`
(gVisor/Kata) and `wasmcloud.md` (WASM components), and is now the substrate several
agent-hosting platforms — notably AWS Bedrock AgentCore (`aws-agents.md`) — use for
per-session/per-tenant agent sandboxing, since agent code execution is treated as inherently
untrusted and often long-lived-but-idle.

## Key findings

- **Origin**: a VMM using Linux KVM, written in Rust, developed inside AWS and open-sourced in
  November 2018, purpose-built to replace per-customer EC2 instances as the isolation unit for
  Lambda and Fargate. It originated as a fork of Chromium OS's `crosvm` VMM, since diverged.
- **License and governance**: Apache License 2.0 (crosvm-derived sections under BSD-3-Clause).
  Governance is AWS-controlled, not an independent foundation — the repo's charter states
  maintainers are subject to the project's mission and tenets, with maintainers predominantly
  AWS-affiliated. There is no CNCF/Linux Foundation transfer; it's "an AWS open source project
  that encourages contributions" — closer to a benevolent-vendor model than an independent
  foundation, unlike Kata Containers (OpenInfra/CNCF-adjacent) or gVisor (Google-led but under
  a more neutral GitHub org).
- **Minimal device model**: Firecracker deliberately exposes only 5 emulated devices —
  virtio-net, virtio-block, virtio-vsock, a serial console, and a partial i8042 keyboard
  controller (used only to signal guest-requested reboot/reset) — plus KVM's own
  PIC/IOAPIC/PIT. All legacy PC/BIOS emulation is excluded by design, the direct architectural
  contrast with QEMU.
- **Performance characteristics** (enforced by CI against a formal specification): boot time
  ≤125ms from API call to guest init; memory overhead ≤5 MiB per microVM (1 vCPU/128MiB
  config); microVM creation rate up to 150/second per host (5/core/sec); network throughput up
  to 14.5–25 Gbps depending on CPU budget; ~0.06ms added virtualization latency.
- **Security model — layered defense in depth**: (1) the KVM hardware-virtualization boundary
  itself — a stronger isolation guarantee than a shared-kernel container, architecturally
  distinct from gVisor's approach of reimplementing a subset of Linux syscalls in userspace Go
  rather than running a separate kernel (`k8s-agent-sandbox.md`); (2) per-thread seccomp-bpf
  filters restricting Firecracker's own process to a minimal syscall set (independent research
  counted ~40 allowed syscalls with tight argument filters); (3) the optional `jailer`
  companion process, which sets up cgroups, namespaces, and chroot with elevated privileges,
  then drops privileges and execs into the unprivileged Firecracker binary — a second line of
  defense if the VM boundary itself is ever compromised.
- **Threat containment model**: the design doc explicitly treats every vCPU thread as running
  malicious code the moment it starts, defining nested "trust zones" from least-trusted (guest
  vCPUs) to most-trusted (host), with enforced barriers at I/O boundaries (e.g., all network
  I/O passes through a rate-limited copy from the emulated NIC to the host TAP device).
- **Snapshot/restore (pause-resume)**: Firecracker supports pausing a running microVM, then
  serializing full guest memory + emulated device/KVM state to disk as a snapshot (full or
  incremental "diff" snapshots using KVM dirty-page tracking), which can later be loaded into a
  fresh Firecracker process to resume execution from that exact point. Snapshot loading uses
  copy-on-write memory mapping for fast resume, and a `VMGenID` device notifies the guest
  kernel PRNG that it has resumed from a snapshot (avoiding randomness reuse across clones).
  Directly relevant to agent-session lifecycle: pause an idle agent session to reclaim compute,
  resume later with full memory/process state intact rather than re-initializing the
  container/kernel. Caveats: network/vsock connections don't survive resume cleanly, and
  re-using the same snapshot for multiple resumed VMs is explicitly called out as insecure
  unless the integrator handles unique-identifier de-duplication.
- **Adoption beyond Lambda/Fargate**: production/integration adopters include Fly.io
  (positions itself as using Firecracker for its container-hosting platform, chosen over
  gVisor/Kata/nsjail for the isolation-vs-performance tradeoff), Kata Containers (uses
  Firecracker as one of its VMM backends alongside QEMU/cloud-hypervisor), containerd (via
  `firecracker-containerd`), plus smaller PaaS/CI vendors.
- **Comparison to gVisor/Kata (`k8s-agent-sandbox.md`)**: gVisor is a userspace reimplementation
  of the Linux kernel interface in memory-safe Go — it still shares the host kernel underneath
  but intercepts syscalls, trading a performance hit for eliminating most kernel-attack-surface
  risk without needing virtualization. Kata Containers is architecturally closer to
  Firecracker's approach (real Linux kernel in a lightweight VM) and can alternatively use
  Firecracker itself as its VMM backend — Firecracker and Kata are not strictly competing but
  sometimes composable (Kata-on-Firecracker), mirroring the "sandbox API decoupled from
  isolation runtime" pattern already noted in `k8s-agent-sandbox.md`.
- **Comparison to WASM isolation (`wasmcloud.md`)**: WASM sandboxes sit at the opposite,
  lighter-weight end of the spectrum — isolating by running code inside a language-level
  virtual machine with a restricted capability surface, rather than giving each tenant its own
  kernel. Cheaper and denser than even microVMs, but only works for code compiled to WASM;
  can't run arbitrary Linux binaries/POSIX workloads the way Firecracker can. Firecracker's
  approach is heavier but universal — any Linux guest workload, no code changes required.
- **Relevance to agent runtimes**: the per-session microVM pattern (spin up a fresh,
  disposable, hardware-isolated VM per agent/session, optionally snapshot-pause it when idle,
  resume it later) is exactly the pattern AWS Bedrock AgentCore uses (`aws-agents.md`), and is
  a natural fit for agentic workloads because (a) agent sessions run untrusted/dynamically
  generated code (tool calls, generated scripts) benefiting from VM-grade isolation rather than
  shared-kernel container isolation; (b) sessions are often long-lived-but-idle (waiting on a
  human or an LLM round-trip), making snapshot/pause-resume economically attractive versus
  keeping a live pod/VM running; (c) the boot-time/density numbers make "one microVM per
  session" tractable at scale in a way "one full EC2 instance per session" never was.

## CF relevance

Firecracker is the underlying isolation technology implicitly referenced wherever this
research set discusses "microVM-based session isolation" (AWS Bedrock AgentCore,
`aws-agents.md`) — this note fills that gap with the actual mechanics. For CF, the key
takeaway is that the container→microVM→full-VM isolation spectrum has a well-established,
open-source, hardware-virtualization point (Firecracker) that's specifically optimized for
the "many short-lived, untrusted, possibly-idle sessions" shape that agent workloads exhibit —
a different profile than CF's existing long-lived app-instance model was originally designed
for. The snapshot/pause/resume mechanism is particularly relevant to any CF exploration of
scale-to-zero for agent sessions (complementing `keda.md`'s autoscaling angle): rather than
terminating and cold-starting a full app instance, a Firecracker-style pause/resume could
preserve in-memory agent state across idle periods at container-like density.

## Open questions

- Would a CF-native agent runtime benefit from Firecracker-style per-session microVM
  isolation directly (e.g., via Kata-on-Firecracker on Diego cells), or is this a level of
  isolation only relevant for genuinely untrusted/multi-tenant code execution (tool calls,
  generated scripts) rather than the agent's own orchestration logic?
- Firecracker's snapshot/restore explicitly warns against reusing one snapshot across multiple
  resumed VMs without careful unique-ID handling — how would this constraint interact with a
  CF-native "pause an idle agent session, resume it later" feature if built on similar
  snapshotting technology?
- Given Firecracker's AWS-controlled (not foundation) governance model, is there a risk in
  building CF-native tooling around it directly, versus using it indirectly via
  foundation-governed layers like Kata Containers?
- Is the container→gVisor/Kata→Firecracker→full-VM isolation spectrum something CF should
  formalize as a tiered sandboxing model (letting operators or workload authors choose a
  point on the spectrum per use case), similar to how `k8s-agent-sandbox.md` already frames
  gVisor/Kata as swappable backends behind one sandbox API?
