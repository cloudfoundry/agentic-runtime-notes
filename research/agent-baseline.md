---
title: "Agent Baseline: Six Security Outcomes for Enterprise AI Agents"
author: Ruben Koster (@rkoster)
date: 2026-09-18
tags: [authorization, sandboxing, observability-governance, ecosystem-survey]
cf_areas: [uaa, capi, diego, loggregator]
status: draft
ratings:
  platform-impact:
    value: 89
    note: "The baseline turns broad agent security concerns into discoverable outcomes, controls, and evidence that a platform could operationalize."
  maturity:
    value: 48
    note: "Agent Baseline is explicitly a working draft open for public comment rather than a finalized standard."
  novelty:
    value: 68
    note: "The six-outcome structure connects identity, runtime constraints, authorization, evidence, validation, and response into one agent-specific framework."
  actionability:
    value: 86
    note: "The controls provide a practical checklist for mapping existing CF primitives to missing agent-specific security capabilities."
sources:
  - https://agentbaseline.org/
  - https://agentbaseline.org/controls
  - https://agentbaseline.org/whitepaper.pdf
  - https://github.com/agentbaseline/agentbaseline
---

## Summary

Agent Baseline is an open-source draft framework describing six security outcomes an enterprise
must achieve to run AI agents: Discover, Constrain, Authorize, Observe, Validate, and Respond.
It contains 35 controls that state required capabilities and evidence rather than prescribing a
single product architecture. For Cloud Foundry, the baseline is a useful assessment lens for
identifying which platform primitives already exist and which agent-specific inventory, policy,
provenance, evaluation, and response capabilities remain to be built.

## Key findings

- **The framework starts from a distinct agent threat model.** Agents are runtime-programmable
  through natural-language instructions, can access real data and tools, and may act with
  limited human supervision. Existing application and infrastructure security remains necessary
  but does not fully answer what an agent is allowed to do or how its actions are evidenced.
- **Discover establishes inventory and accountability.** The baseline requires an accurate view
  of agents and dependencies, including components, owners, operating status, and effective
  access. A platform cannot constrain or respond to an agent it cannot identify or inventory.
- **Constrain limits the execution surface.** Controls address the agent's components, runtime,
  data, capabilities, environments, and network reach. This aligns with sandboxing, service
  bindings, egress policy, and least-privilege runtime configuration.
- **Authorize binds action to context.** Authorization is not just a user or workload identity;
  it connects identity, task, target, authority, resource, action, and time. This supports
  scoped agent delegation and limits authority by purpose rather than granting a broad token.
- **Observe requires correlated evidence.** The baseline asks operators to connect intent,
  identity, task, policy, tool use, action, and outcome. Plain process logs are insufficient when
  an agent chains model calls, tools, subagents, and external effects.
- **Validate governs admission and change.** Agents and their components should be evaluated
  before use, after material changes, and at intervals appropriate to risk. This includes
  implementation, configuration, tool, model, and runtime changes rather than only a one-time
  application deployment check.
- **Respond makes stopping and evidence preservation explicit.** The framework includes stop,
  revoke, quarantine, scope-impact, evidence-preservation, and determination-of-impact
  capabilities. Response is a runtime control, not only an incident-management document.
- **The controls are evidence-oriented.** Agent Baseline describes what an enterprise must be
  able to demonstrate, allowing different implementations to satisfy the same outcome. This
  makes it suitable for platform capability mapping and assurance discussions, but leaves
  evidence formats and ownership to adopters.
- **The status is intentionally provisional.** The website describes the baseline as a working
  draft for community review and invites implementation feedback. It should be treated as a
  structured proposal, not a finalized compliance standard.

## CF relevance

Cloud Foundry already provides pieces of the baseline. CAPI can inventory applications and
owners; Diego manages process lifecycle and desired state; UAA and instance identity provide
identity primitives; networking and service bindings constrain access; and Loggregator provides
operational event streams. Those primitives can support parts of Discover, Constrain,
Authorize, and Observe, but they do not automatically describe agent intent, tool authority,
model/component provenance, or delegated task scope.

The baseline suggests an agent security layer above ordinary CF applications. That layer could
register agent components and effective access, issue task- and resource-scoped authority,
enforce sandbox and egress policy, correlate model/tool/action events, and trigger revocation or
quarantine. CAPI and Diego events could feed inventory and response workflows, while UAA or a
delegation broker could supply identity. Loggregator would need correlation conventions for agent,
task, tool, policy, and outcome identifiers.

Validate and Respond are the clearest gaps. CF buildpacks and deployment pipelines can validate
artifacts, but agent-specific evaluation, prompt/tool policy, model changes, runtime drift,
kill/revoke/quarantine, and evidence preservation require additional services or conventions.
The baseline is therefore useful less as a product to install than as a checklist for deciding
which capabilities belong in the CF platform, a brokered agent service, or application teams.

## Open questions

- Which Agent Baseline controls can CF satisfy with existing CAPI, Diego, UAA, networking,
  service bindings, and Loggregator, and which require new platform services?
- What is the authoritative inventory of agent versions, models, prompts, tools, permissions,
  owners, and effective access across orgs and spaces?
- How should task-scoped authority and delegated agent identity be represented and revoked?
- Which evidence should be retained for an agent action, and how should it correlate intent,
  policy, tool calls, resources, outcomes, and human approvals without storing sensitive content?
- Where should agent evaluation and revalidation run: build pipelines, admission controllers,
  runtime gateways, or an external assurance service?
- What is the minimum response path for stopping a running agent, removing authority,
  quarantining its workspace, preserving evidence, and determining impact?
- Should CF adopt the baseline as guidance, map it into platform service-level objectives, or use
  it to evaluate independently deployed agent platforms?
