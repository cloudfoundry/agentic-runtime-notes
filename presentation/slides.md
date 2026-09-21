---
marp: true
theme: cloud-foundry
title: Agentic Runtime Working Group
description: From research to sandboxing proofs of concept
paginate: true
footer: Cloud Foundry Summit 2026 · Agentic Runtime Working Group
---

<!-- _class: title -->
# Agentic Runtime
## From research to sandboxing POCs

**Working Group update**  ·  Cloud Foundry Summit 2026

<!--
We started by asking a broad question: what does Cloud Foundry need to make
agentic workloads first-class? In a few months, the group has moved from
open-ended research to a first practical boundary: sandboxing.
-->

---

<div class="eyebrow">The mission</div>

# Make agents feel native

The Agentic Runtime Working Group is exploring how AI agents and LLM-powered
workloads can be **deployed, managed, secured, scaled, and observed** with
Cloud Foundry's platform primitives.

<div class="callout"><strong>Not a product roadmap yet.</strong><br>We are building shared context before we build a settled answer.</div>

<!--
This is a working group, not a team arriving with a finished architecture.
The first phase is intentionally broad: bring in ideas, research the wider
ecosystem, and let the themes emerge from what people contribute.
-->

---

<div class="eyebrow">Momentum</div>

# Research to POCs

![w:1060](assets/timeline.svg)

<div class="source">Repository snapshot, 20 Sep 2026 · 63 PRs total · 43 merged · 20 open · 3 open issues · github.com/cloudfoundry/agentic-runtime-notes</div>

<!--
The shape is the story. One pull request in June became eleven in July,
twenty-nine in August, and twenty-two so far in September. The repository
snapshot is 63 PRs: 43 merged and 20 open. The workshop turned that activity
into a priority: sandboxing first, with a Summit POC target.
-->

---

<div class="eyebrow">The workshop output</div>

# Seven clusters. One first move.

<div class="priority">
  <div><b>01</b> Sandboxing</div>
  <div><b>02</b> Identity & credentials</div>
  <div><b>03</b> Observability / OTel</div>
  <div><b>04</b> MCP facilitation</div>
  <div><b>05</b> Agent ↔ app communication</div>
  <div><b>06</b> Agentic buildpacks</div>
  <div><b>07</b> Durable workloads</div>
</div>

<p class="subtitle">The themes emerged from contributions. The order is where we chose to start.</p>

<!--
The group clustered the material and agreed an order. Sandboxing came first,
then identity and credentials, observability, MCP, agent-to-app communication,
buildpacks, and durable workloads. This is a sequence for exploration, not a
claim that the platform has seven final feature areas.
-->

---

<div class="eyebrow">A shared model</div>

# What is an agentic workload?

![w:960](assets/agent-loop.svg)

<p class="callout">Every arrow here is a network call to a bound service — <em>except the bottom right one</em>.</p>

<!--
Mechanically an agent is not exotic. //

There is one process running a loop.
It builds a prompt, and sends it to a model.
The model is reached over the network, with credentials.
That is a service binding. //

The model cannot do anything by itself.
It answers with text that says: please call this tool.
The agent loop is what actually executes that call,
and feeds the result back into the next prompt. //

Many of those tools are remote too — MCP over HTTP, or a plain API.
Also a binding. //

The loop also has to remember. Conversation history, checkpoints,
enough state to resume a run that was interrupted.
Some harnesses are starting to keep that in a database
instead of in memory or on local disk.
When they do, that is a binding as well. //

So look at the picture. Model: binding. Session state: binding.
Remote tools: binding. Loop: a process. //

Everything is a network call to a bound service.
Except the box on the bottom right.
-->

---

<div class="eyebrow">The bridge</div>

# Agents are 12-factor apps

| Twelve-factor concern | In an agent | On Cloud Foundry today |
| --- | --- | --- |
| Backing service | the LLM endpoint | service binding |
| Backing service | remote MCP tools | binding or route |
| Backing service | session and run state | database binding |
| Config | model, keys, limits | env and `VCAP_SERVICES` |
| Processes | the agent loop | an ordinary app process |
| Disposability | resume or retry a run | restart, scale, health checks |
| Execution | local tools: shell, files, code | no primitive yet |

<p class="subtitle">Six of these we already know how to run. The seventh is why the group started with sandboxing.</p>

<!--
So let's be concrete about that claim. //

Take the twelve-factor checklist we already apply to every app on this platform.

The model endpoint is a backing service. We bind to it.
Remote MCP tools are backing services. We bind to those too.
Session and run state belongs in a database, which is another binding.
Model choice, keys and limits are config, from the environment.
The agent loop is just a process.
And a run that can be retried or resumed is ordinary disposability. //

Six out of seven are solved problems. We have been doing them for a decade. //

The last row is the one with nothing in the right-hand column.
Local execution. Shell, files, generated code.
There is no platform primitive for it. //

That single gap is the whole reason sandboxing came first.
-->

---

<div class="eyebrow">The first platform boundary</div>

# Local execution breaks the model

<div class="loop">
  <div class="loop-node">Agent</div><div class="loop-arrow">→</div>
  <div class="loop-node highlight">Local machine</div><div class="loop-arrow">→</div>
  <div class="loop-node">Files</div>
</div>

<ul>
  <li>Which identity is acting?</li>
  <li>Which credentials and network paths are available?</li>
  <li>What gets isolated, observed, stopped, or cleaned up?</li>
</ul>

<blockquote>To make the tool cloud-native, make execution an explicit managed boundary.</blockquote>

<!--
Once the tool can execute locally, the platform has to answer new questions:
whose identity is acting, which credentials it can see, where it can connect,
and how we stop and observe it. The answer cannot be an invisible process on
some host. Execution needs to become an explicit boundary.
-->

---

<div class="eyebrow">Why sandboxing first</div>

# A sandbox makes the boundary real

<div class="loop">
  <div class="loop-node">Agent</div><div class="loop-arrow">→</div>
  <div class="loop-node highlight">Exec service</div><div class="loop-arrow">→</div>
  <div class="loop-node">Isolated work</div>
</div>

<div class="metric-grid">
  <div class="metric"><b>Isolate</b><span>processes and files</span></div>
  <div class="metric"><b>Govern</b><span>identity and policy</span></div>
  <div class="metric"><b>Observe</b><span>actions and output</span></div>
  <div class="metric"><b>Manage</b><span>lifecycle and cleanup</span></div>
</div>

<p class="source">OpenSandbox research: PR #57 · AAIF project proposal #26 (open proposal, not an adopted architecture)</p>

<!--
That is why sandboxing is the first POC focus. A sandbox or exec service gives
the local-looking action a boundary the platform can govern. We researched
OpenSandbox as useful prior art. It is linked to an open AAIF project proposal,
not presented here as an adopted AAIF project or as our chosen architecture.
-->

---

<div class="eyebrow">A conversation with the POC leads</div>

# Demo placeholder

![w:1000](assets/developer-journey.svg)

<div class="source">Developer journey from the CF Herdr POC — one implementation under discussion, not an adopted architecture.</div>

<p class="subtitle">The point of the demo: make the execution boundary tangible.</p>

<!--
This slide is intentionally a placeholder. We will choose the scenario with
the other leads. //

What the demo should show is the developer experience, not an architecture.
Choose the work. Start an agent in its own workspace.
Steer it from anywhere — observe, prompt, review.
Then ship the result through Cloud Foundry like any other change. //

This journey is taken from the CF Herdr POC. It is one implementation,
shown to make the boundary tangible. It is not a working group decision,
and the scenario itself is still open.
-->

---

<div class="eyebrow">Join the next phase</div>

# Bring a question. Test a boundary.

<ul>
  <li>Help test and shape the sandboxing POCs.</li>
  <li>Add research or an idea for the next clusters.</li>
  <li>Connect the work across Cloud Foundry, MCP, and AAIF communities.</li>
</ul>

<blockquote>Build the concrete thing early. Keep the answer open long enough for the community to improve it.</blockquote>

<p><strong>cloudfoundry.github.io/agentic-runtime-notes</strong></p>

<!--
The ask is participation: help us test the sandboxing POCs, add research for
the next clusters, and continue the cross-foundation conversation. We have
enough momentum to make the question concrete, but not enough certainty to
pretend the answer is settled.
-->
