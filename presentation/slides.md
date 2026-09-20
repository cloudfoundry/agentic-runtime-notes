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

<div class="timeline">
  <div class="timeline-track"></div>
  <div class="timeline-events">
    <div class="timeline-event"><div class="timeline-date">25 JUN</div><div class="timeline-dot"></div><div class="timeline-label">Process bootstrapped<br>PR #1</div></div>
    <div class="timeline-event"><div class="timeline-date">JUL–AUG</div><div class="timeline-dot"></div><div class="timeline-label">Research accelerates<br>40 merged PRs</div></div>
    <div class="timeline-event"><div class="timeline-date">03 SEP</div><div class="timeline-dot"></div><div class="timeline-label">Workshop prioritizes<br>sandboxing</div></div>
    <div class="timeline-event"><div class="timeline-date">12–13 SEP</div><div class="timeline-dot"></div><div class="timeline-label">AgntCON / MCPcon<br>Amsterdam</div></div>
    <div class="timeline-event"><div class="timeline-date">17–19 SEP</div><div class="timeline-dot"></div><div class="timeline-label">Focused research<br>and POC preparation</div></div>
  </div>
</div>

<div class="activity-ribbon">Repository snapshot · 63 PRs total · 43 merged · 20 open · 3 open issues</div>
<div class="source">Sources: github.com/cloudfoundry/agentic-runtime-notes · workshops/02-09-2026-workshop-minutes.md</div>

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

<div class="loop">
  <div class="loop-node">Goal</div><div class="loop-arrow">→</div>
  <div class="loop-node">Agent</div><div class="loop-arrow">→</div>
  <div class="loop-node highlight">LLM</div><div class="loop-arrow">→</div>
  <div class="loop-node highlight">Tool</div><div class="loop-arrow">→</div>
  <div class="loop-node">Result</div>
</div>

<p class="callout">An app answers a request. An agent can <strong>choose an action, observe the result, and continue the loop</strong>.</p>

<!--
An agent is not just an immature application. The useful distinction is the
loop: a goal, an LLM helping choose the next action, a tool, an observed result,
and another turn. That loop makes the runtime boundary more important.
-->

---

<div class="eyebrow">The awkward tool</div>

# Some tools are not APIs

<div class="boundary">
  <div class="boundary-remote">
    <h3>Remote service</h3>
    <p>Call an API. Send credentials. Receive a result. A familiar cloud-native boundary.</p>
    <code>agent → service → result</code>
  </div>
  <div class="boundary-local">
    <h3>Local execution</h3>
    <p>Run commands, edit files, execute generated code, or drive a browser.</p>
    <code>agent → process + files + network</code>
  </div>
</div>

<p class="subtitle">Many agent tools grew up close to a developer's desktop. That is useful, but it is not yet a managed runtime boundary.</p>

<!--
Tools such as a database API are easy to make remote. Other tools need an
execution environment: a shell, files, generated code, or browser automation.
Those patterns often started as local desktop tools. The challenge is not that
agents are simply immature; it is that local execution carries a lot of state.
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

<div class="demo-placeholder">
  <div><strong>Sandboxed agent execution</strong><span>Final scenario to be selected with the POC leads.</span></div>
</div>

<p class="subtitle">The point of the demo: make the execution boundary tangible.</p>

<!--
This slide is intentionally a placeholder. We will choose the scenario with
the other leads. Whatever we show should make the boundary tangible, not imply
that the working group has already settled the architecture.
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
