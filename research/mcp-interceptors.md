---
title: "MCP Interceptors: Reusable Policy and Context Mediation"
author: Ruben Koster (@rkoster)
date: 2026-09-18
tags: [authorization, observability-governance, inter-agent-comms, ecosystem-survey]
cf_areas: [uaa, capi, diego, loggregator]
status: draft
ratings:
  platform-impact:
    value: 85
    note: "Reusable interception could consolidate redaction, validation, authorization, and audit across CF-hosted agent gateways and MCP services."
  maturity:
    value: 40
    note: "The working group and extension repository are experimental, with the main proposal still in draft and several deliverables ideating."
  novelty:
    value: 75
    note: "The proposal makes cross-cutting agent context mediation a discoverable protocol primitive rather than bespoke middleware per client or gateway."
  actionability:
    value: 82
    note: "Validator/mutator and deployment models map directly to CF gateway, sidecar, policy, and audit integration points."
sources:
  - https://modelcontextprotocol.io/community/working-groups/interceptors
  - https://github.com/modelcontextprotocol/experimental-ext-interceptors
  - https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1763
  - https://github.com/modelcontextprotocol/modelcontextprotocol/pull/2624
---

## Summary

The MCP Interceptors Working Group is exploring a protocol-level primitive for inspecting,
validating, and transforming context at key points in the agentic lifecycle. The proposal
distinguishes validators, which return pass/fail decisions, from mutators, which transform
payloads, and supports hooks around tools, resources, prompts, sampling, and elicitation. For
Cloud Foundry, interceptors could provide reusable policy and audit mediation across gateways,
sidecars, and remote services, but the work remains experimental.

## Key findings

- **The motivation is an M x N integration problem.** Agent ecosystems are accumulating bespoke
  sidecars, proxies, and gateways for redaction, validation, policy, and auditing. These
  integrations are difficult to reuse across clients and transports. The working group aims to
  define a common MCP-facing interface.
- **There are two core interceptor types.** Validators inspect an operation or context and return
  a pass/fail decision. Mutators transform context payloads, such as redacting PII or normalizing
  data before it reaches a model, tool, or client.
- **Hooks cover the agent lifecycle.** The charter identifies tool invocations, resource access,
  prompt handling, sampling, and elicitation, with possible extension to LLM completions and
  application-specific workflows. This broadens interception beyond ordinary HTTP middleware.
- **Trust boundaries are part of the design.** An interceptor may run in-process, as a sidecar,
  or as a remote service. The deployment model changes what the interceptor can trust, what data
  crosses a boundary, how identity and policy are conveyed, and how failures affect the operation.
- **Ordering and composition matter.** The proposal includes priority-based chain ordering. A
  redaction mutator, schema validator, authorization validator, and audit interceptor can produce
  different results depending on order, so chains require explicit configuration and evidence.
- **Audit mode is a first-class concern.** Interceptors may inspect or record without changing
  the operation, supporting audit logging and policy analysis. Operators still need to protect
  sensitive payloads and distinguish observed data from authoritative outcomes.
- **Reference use cases are concrete.** The working group identifies sample interceptors for PII
  redaction, schema validation, and audit logging, plus SDKs, a common sidecar/proxy runtime,
  and a CLI for invocation and testing.
- **The proposal is experimental.** The working group charter and experimental repository do not
  establish a finalized MCP standard. The main SEP and shared runtime remain under development,
  so implementations should expect interface and semantics changes.
- **Interceptors are not general middleware.** The stated goal is an MCP/context protocol
  interface, not a replacement for every HTTP proxy or client-specific hook engine. Transport
  and session behavior remain coordinated with other MCP working groups.

## CF relevance

Cloud Foundry could use interceptors at several layers. An MCP or AI gateway could run policy
validators before tool calls, a sidecar could redact or validate payloads near an agent process,
and a remote service could apply centrally managed organization or space policy. UAA or workload
identity could supply the principal and agent context, while CAPI/Diego metadata could identify
the application, instance, space, or task.

The protocol may reduce duplicated platform middleware. A CF foundation could publish approved
interceptors for authorization, PII handling, schema validation, cost tagging, and audit, with
deployment choices based on latency and sensitivity. Loggregator could receive correlation events
for interceptor decisions, mutations, denials, and downstream outcomes. However, mutators create
accountability requirements: the system must preserve what changed, why, under which policy, and
which payload reached the model or tool.

The main integration choices are ownership and failure semantics. Platform-controlled gateways
can enforce organization-wide policy but see more traffic; app-local sidecars reduce central
coupling but increase deployment burden; remote interceptors are reusable but add latency and
availability dependencies. CF would need explicit fail-open/fail-closed behavior, chain ordering,
tenant isolation, policy distribution, and sensitive-data handling.

## Open questions

- Which interceptor hooks should be platform-managed versus application-managed in CF?
- How should interceptor identity and authorization work for users, agent instances, tools, and
  delegated subagents?
- What ordering, timeout, retry, and failure semantics apply when a validator or mutator is
  unavailable or returns malformed output?
- How should CF record mutation provenance so operators can prove which payload reached a model
  or tool?
- Should interceptors fail closed for authorization and validation but permit degraded operation
  for optional audit or redaction paths?
- How should sensitive prompts, resource contents, tool arguments, and model responses be
  redacted before logging or remote interception?
- Can a common interceptor chain span MCP gateways, model gateways, and CF application workflows
  without creating another platform-specific M x N integration problem?
