---
title: Durable execution as a CF-native primitive — what tasks are missing
author: Ruben Koster (@rkoster)
date: 2026-08-11
tags: [runtime-lifecycle, orchestration]
---

## The idea

Cloud Foundry has no durable execution primitive. `cf run-task` runs a process once: it cannot
checkpoint, cannot resume, cannot retry with backoff, cannot be scheduled, and cannot be woken
by an external event. App instances are the opposite extreme — long-running processes with no
durable per-instance state, deliberately treated as cattle. Between "runs once and dies" and
"runs forever" there is nothing, and durable execution lives exactly in that gap.

Every AI agent framework surveyed in this repo needs durable execution. Strikingly, **none of
them ship it** — they all expose a pluggable interface and delegate to a substrate. Google ADK
provides replay-safe primitives but no engine. The OpenAI Agents SDK relies on external
Temporal or Dapr integrations. Microsoft Agent Framework binds to Azure Durable Task. LangGraph
has checkpointers, CrewAI has storage providers, LlamaIndex serializes a `Context`. That is a
consistent, unexploited seam: the ecosystem is asking a platform to provide something CF
doesn't have.

The proposal is not to build a workflow engine. It is to add the one verb CF is missing:
**"I have checkpointed my state — release my container, and bring me back on this event or at
this time."**

## The gap, concretely

Across the frameworks in this repo, the requirements converge on six things:

| Requirement | Framework evidence | CF today |
|---|---|---|
| Durable per-entity state surviving process death | LangGraph checkpointers, CrewAI `@persist`, LlamaIndex `Context` serialization, Temporal event history | App must build it on a bound service; no platform notion |
| Address a specific execution by stable ID | Temporal workflow ID, LangGraph `thread_id`, Dapr instance ID, CrewAI `restore_from_state_id` | **None** — a task GUID is minted per run, not developer-supplied |
| Indefinite pause/resume for human-in-the-loop | Temporal Signals, Dapr `wait_for_external_event`, LangGraph `interrupt()`, LlamaIndex `wait_for_event` | **None** — a paused workload must hold a container |
| Durable timers / "wake me later" | Dapr reminders, Temporal timers, Cloudflare alarms | **None** — no scheduler primitive at all |
| Idempotent step execution with retries | Temporal activity retries, Dapr `WorkflowRetryPolicy`, LangGraph superstep boundaries | **None** — task failure is terminal |
| Long-running-but-idle economics | The dominant agent shape: waiting on an LLM or a human | **None** — idle costs the same as busy |

The economics row is the one that is specific to CF rather than generic. An agent waiting three
days for a human approval occupies a full app instance today, doing nothing. Dapr Agents
describes this pause as lasting "seconds to days without holding a process open"; Temporal's
human-in-the-loop Signal "survives Worker restarts/crashes." CF has no way to express that at
all — which means the platform charges full price for waiting.

## CF has already solved half of this

State persistence is not the gap. A CF app using LangGraph's `PostgresSaver` against a bound
Postgres, or CrewAI's SQLite checkpointer, or an OpenAI Agents SDK `SQLAlchemySession`, is
already persisting exactly the right thing, in exactly the CF-idiomatic way: state lives in a
bound backing service, and the workload stays stateless.

That should stay true. **CF should own the durable execution lifecycle; a bound service should
own the durable state.** CAPI and Diego never become a database, the checkpoint store stays
pluggable and operator-chosen like any marketplace service, and the platform stores nothing
larger than a pointer.

What is missing is only the lifecycle: nothing lets a workload say *"I've checkpointed — release
my container and wake me later."* That single verb is the whole idea.

## Tasks are the right execution primitive, but the wrong identity primitive

The obvious move is to extend `cf run-task`. Half of that instinct is right and half is wrong.

**Right:** Diego already has a first-class Task abstraction distinct from LRPs — short-lived,
run-to-completion, container released on exit. That is precisely the execution shape for a slice
of work between two suspensions. LRPs are the wrong shape, because they are designed to run
forever, and "runs forever" is what durable execution exists to avoid.

**Wrong:** a CF task is not addressable. Its GUID is minted per run rather than supplied by the
developer, so there is no way to say "resume the execution for order-123." And a task has no
route, no port, and no way to be sent anything. Every resume path in every framework is
addressed — Temporal Signals target a workflow ID, LangGraph's `Command(resume=...)` targets a
`thread_id`, Dapr's `wait_for_external_event` targets an instance ID. An approval webhook has to
say *which* execution was approved.

So identity has to live above tasks, not inside them — the same split Temporal makes between a
durable, addressable *workflow execution* and the ephemeral *workflow tasks* that advance it:

- **A durable execution resource in CAPI** — developer-supplied ID, current state, pending
  resume conditions, retry policy, and an opaque pointer to state in the bound service. This is
  the addressable, durable thing, and it is cheap: a row, not a container.
- **Diego Tasks as compute slices** — each advances the execution from one suspension to the
  next, then exits. Between slices no container exists. Tasks stay exactly what they are today;
  they simply stop being the unit of identity.
- **Events delivered to the CAPI resource**, which schedules a fresh Diego Task to resume,
  handing it the event payload and the state pointer.

## Interface: one API per cell, not one per container

A workload needs some way to say "checkpoint saved, suspend me." A per-container helper process
(the model the Envoy container proxy established for route integrity) is one option, but it is
the wrong trade here.

The distinction is whether the helper holds per-app state. A Dapr sidecar must be per-container,
because it holds app-specific component config and serves building-block APIs under the app's
identity. A durable-execution API holds nothing: it is a thin control call — "here is my state
pointer, here is my resume condition, suspend me." Paying for that per container buys nothing.

CF already has a precedent for the per-host shape: the **Loggregator agent** runs once per Diego
cell and every container on that cell talks to it. A durable-execution API fits that pattern —
one process per cell, shared by every container on it, patched once per cell, and not charged
against any app's memory allocation.

Because a per-cell API is multi-tenant across orgs and spaces, it needs to authenticate callers.
The answer is the one CF already has: the workload connects over mTLS with its **Diego instance
identity certificate**, and the agent extracts `OU=app:`, `OU=space:`, and `OU=organization:`
to authorize the call and scope the execution's identity. This is the same identity extraction
[RFC-0055](https://github.com/cloudfoundry/community/blob/main/toc/rfc/rfc-0055-identity-aware-routing-for-gorouter.md)
specifies for GoRouter, applied to a host-local API instead. No new credential, no SDK per
buildpack language — a `curl` against a well-known local address is enough.

## What CF would deliberately not own

- **No workflow DSL and no orchestration semantics.** CF does not define steps, graphs, or
  control flow. The framework or the application does. CF only suspends and resumes.
- **No state storage.** State goes to a bound service; CF stores a pointer.
- **No execution guarantees beyond at-least-once.** Resumed work may re-run; idempotency is the
  workload's responsibility, exactly as it already is in LangGraph, where a resumed node
  re-executes from its start.
- **No HTTP-addressable resume.** See below — the framework evidence does not ask for it.

Staying this narrow is what keeps it a primitive rather than a framework, and what lets
Temporal, Dapr Workflows, LangGraph, and hand-written code all sit on top of the same thing.

## The road not taken: waking on an incoming request

It is tempting to require that a suspended execution be reachable by HTTP, so a request revives
it — Cloudflare's model, where a hibernating Durable Object rehydrates on the next incoming
request or WebSocket message. That would need something CF does not have: a component that holds
the request while the execution is reconstituted (Knative's activator, KEDA's HTTP interceptor —
see `keda.md`).

The framework evidence does not support making this a requirement:

| Framework | How a suspended execution is resumed | Inbound endpoint on the execution? |
|---|---|---|
| Temporal | Signal to the Temporal *service*; Workers poll task queues outbound and "don't need any inbound network exposure" | No |
| LangGraph | `Command(resume=value)` against the same `thread_id`, via the runtime | No |
| LlamaIndex | `ctx.wait_for_event(...)` + `send_event`; long waits serialize the `Context` | No |
| CrewAI | `kickoff(id=...)` / `restore_from_state_id` — a library call | No |
| OpenAI Agents SDK | `result.to_state()` → `state.approve(...)` → re-run | No |
| Letta | Agents addressed by ID behind an always-on App Server | Server yes, execution no |
| Cloudflare Agents | Durable Object rehydrates on incoming request | **Yes — the exception** |

The near-universal pattern is that a durable execution is addressed **by stable ID through an
always-on service**, and the execution itself is never a network endpoint. Cloudflare differs
because a Durable Object is simultaneously the compute unit, the state store, and the addressing
unit — a property of that runtime, not a requirement of the workload.

Temporal is the sharpest counter-evidence: no inbound exposure for Workers is an explicit
selling point, and its human-in-the-loop Signal survives Worker restarts precisely because the
wait lives in the service rather than in a process.

For CF this means the HTTP front door stays an ordinary app — a routable LRP that calls the
durable-execution API by ID, which is exactly what LangGraph's Agent Server,
`llama-agents-server`, and Letta's App Server already are. The economics still work, because the
expensive thing is the suspended execution idling for hours or days, not a lightweight always-on
front door. Temporal makes the identical trade: service always on, workers ephemeral.

Worth revisiting if request-driven revival turns out to matter for a use case the frameworks
don't currently represent.

## Why it might matter

"Which durable execution substrate do CF apps get?" is a question CF has to answer regardless of
which agent framework a developer picks, because every framework delegates it. Today the answer
is "bring your own, and pay for a container while it waits." Answering it with a CF-native
primitive — rather than by adopting someone else's engine — keeps the platform's existing
contracts intact: stateless workloads, state in bound services, operator-chosen backing
services, and identity from the instance certificate CF already issues.

It would also close CF's missing-scheduler gap as a side effect. Durable timers are needed for
the "wake me later" case anyway, and a platform that can wake a suspended execution at a given
time can schedule a task at a given time.

## What to research next

- What does the checkpoint pointer actually need to contain for each framework's existing
  interface (LangGraph checkpointer, CrewAI storage provider, LlamaIndex `Context`, OpenAI
  Agents SDK session) to map cleanly onto it? If it does not map to all of them, the abstraction
  is wrong.
- How expressive do resume conditions need to be — a timer and a named event, or something
  richer (queue message, service-broker callback, another execution completing)?
- What are the semantics when the bound state service is unavailable at resume time: fail the
  execution, retry with backoff, or hold it suspended?
- Does an execution's identity need to be unique per app, per space, or globally, and what
  happens to in-flight executions across `cf push`, restage, and blue/green?
- How much of Diego's existing Task path is reusable for a resumable slice, and what does the
  per-cell agent need from rep/executor that Loggregator's agent does not?
- Is at-least-once with workload-side idempotency an acceptable contract, or will workloads
  expect exactly-once badly enough that it becomes a support problem?

## Related

- Research notes: `temporal.md` (workflow-execution vs. workflow-task split, polling Workers,
  Signals), `cloudflare-agents.md` (hibernation and request-driven rehydration — the road not
  taken), `langgraph.md` (checkpointers, `interrupt()`, resumed-node idempotency),
  `llamaindex.md` and `crewai.md` (checkpoint/resume in frameworks that ship no engine),
  `google-adk.md` and `openai-agents-sdk.md` (frameworks that explicitly delegate durability),
  `orleans.md` (an alternative model where identity and durability live in the compute
  primitive), `keda.md` (scale-to-zero and the request-holding component this idea avoids
  needing).
- Sibling ideas exploring the adopt-Dapr path to the same capability:
  [[dapr-durable-execution-on-cf]] and [[dapr-aware-gorouter]]. This idea is deliberately
  argued on framework evidence alone rather than as a counterproposal to those.
- [RFC-0055: Identity-Aware Routing for GoRouter](https://github.com/cloudfoundry/community/blob/main/toc/rfc/rfc-0055-identity-aware-routing-for-gorouter.md)
  — the identity extraction reused here for a host-local API.
