---
title: "AWS Strands Agents & Bedrock AgentCore — Framework and Managed Runtime"
author: Ruben Koster (@rkoster)
date: 2026-08-10
tags: [orchestration, inter-agent-comms, observability-governance, sandboxing-isolation, identity, ecosystem-survey]
cf_areas: []
status: draft
sources:
  - https://github.com/strands-agents/sdk-python
  - https://strandsagents.com/
  - https://strandsagents.com/docs/user-guide/quickstart/overview/
  - https://strandsagents.com/docs/user-guide/concepts/agents/agent-loop/
  - https://strandsagents.com/docs/user-guide/concepts/tools/mcp-tools/
  - https://strandsagents.com/docs/user-guide/concepts/multi-agent/agents-as-tools/
  - https://strandsagents.com/docs/user-guide/concepts/multi-agent/agent-to-agent/
  - https://strandsagents.com/docs/user-guide/concepts/model-providers/
  - https://strandsagents.com/docs/user-guide/observability-evaluation/observability/
  - https://strandsagents.com/docs/user-guide/evals-sdk/quickstart/
  - https://aws.amazon.com/bedrock/agentcore/
  - https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/what-is-bedrock-agentcore.html
  - https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agents-tools-runtime.html
ratings:
  platform-impact:
    value: 78
    note: 'Initial review of AWS Strands Agents & Bedrock AgentCore — Framework and Managed Runtime: its subject and tags indicate how broadly the capability could affect an agentic platform.'
  maturity:
    value: 76
    note: 'Initial review of AWS Strands Agents & Bedrock AgentCore — Framework and Managed Runtime: this score reflects the amount of established external practice visible in the note.'
  novelty:
    value: 62
    note: 'Initial review of AWS Strands Agents & Bedrock AgentCore — Framework and Managed Runtime: this score reflects how distinct or emerging the approach appears in the current landscape.'
  actionability:
    value: 66
    note: 'Initial review of AWS Strands Agents & Bedrock AgentCore — Framework and Managed Runtime: this score reflects how readily the material could guide a focused experiment or follow-up.'

---

## Summary

AWS's agentic AI offerings split along the "framework vs. hosting" line seen elsewhere in
this survey. **Strands Agents** is an Apache-2.0, open-source, model-driven agent-building
SDK (Python + TypeScript, single monorepo) comparable to Dapr Agents, Microsoft Agent
Framework, and Google ADK. **Amazon Bedrock AgentCore** is AWS's managed, serverless *hosting*
platform for agents — regardless of which framework built them — directly comparable to the
managed-agent-hosting model already covered in `azure-hosted-agents.md` and
`anthropic-managed-agents.md`. AgentCore decomposes into modular services (Runtime, Harness,
Memory, Gateway, Identity, Observability, Policy, and more), with microVM-based per-session
isolation as its core security primitive.

## Key findings

### Strands Agents

- **License, governance, repo structure**: Apache-2.0, developed by AWS under the
  `strands-agents` GitHub org. The repo was renamed to a monorepo (`harness-sdk`) containing
  both a Python SDK and a TypeScript SDK, plus published governance/tenet docs and a design
  proposal process — signaling a maturing open-source project (~6.9k GitHub stars) rather than
  an AWS-internal tool with a public mirror.
- **"Model-driven" design philosophy**: minimal orchestration code — `Agent(tools=[...])`
  plus a prompt, with the LLM itself driving the reasoning/tool-call loop rather than the
  developer hand-coding a state machine. An `AgentLoop` concept underpins execution, with
  `Hooks` to intercept/log/redirect any step, plus separate `Interventions` (Cedar-based
  authorization, steering, human-in-the-loop) and `Interrupts` for pausing tool execution
  pending external input.
- **Four distinct multi-agent patterns**: (1) **agents-as-tools** (specialized agents wrapped
  as callable tools, three implementation levels from a direct pass to a hand-written wrapper);
  (2) **Swarm**; (3) **Graph** (explicit workflow graph, can mix local and remote A2A agents as
  nodes); (4) **Workflow**. Notably, remote A2A agents are supported as tools and Graph nodes
  but **not yet in Swarm**, since swarm handoffs rely on tool-based mechanisms A2A doesn't yet
  expose.
- **Genuinely multi-provider, not Bedrock-locked**: first-class support for Amazon Bedrock
  (default), Nova, Anthropic (direct), Google, OpenAI, LiteLLM, Ollama, llama.cpp, LlamaAPI,
  MistralAI, SageMaker, Vercel, Writer, plus a custom-provider extension point. Bedrock is the
  quickstart default purely because credentials are typically pre-configured, not an
  architectural lock-in.
- **MCP support is first-class in both directions**: Strands agents can consume external MCP
  servers as tools, and a companion `strands-mcp` package (same monorepo) lets a Strands agent
  be exposed as an MCP server itself.
- **A2A support is bidirectional and fairly deep**: an `A2AAgent` client class consumes any
  remote A2A-compatible agent (sync/async/streaming, agent-card fetch) usable as a tool or
  Graph node; `A2AServer`/`A2AExpressServer` expose a Strands agent as an A2A service, with
  per-`context_id` conversation isolation via an `agent_factory` pattern (explicitly documented
  as *not* an auth boundary — must be enforced at the transport/gateway layer), interrupt-based
  HITL over A2A's `input_required` task state, and path-based mounting for load-balanced
  container deployments.
- **Observability is OpenTelemetry-native**: traces/metrics/logs are the three telemetry
  primitives, with agent-specific trace content (system prompt, model params, token usage per
  model-invocation span; tool input/output per tool-invocation span) and explicit best-practice
  guidance to route through OTel collectors — a stronger native-OTel posture than the OpenAI
  Agents SDK or CrewAI (both covered elsewhere in this research set).
- **Sandbox and Storage are pluggable, first-class concepts**: dedicated "Sandbox" (tool/code
  execution isolation, swappable backends) and "Storage" (session/state persistence, swappable
  backends) concepts, consistent with an "any cloud" positioning rather than assuming AWS.
- **Separate Evals SDK is a notable differentiator** (parallel to Google ADK's built-in eval
  tooling, `google-adk.md`): `strands-agents-evals` ships ~20 built-in evaluators (trajectory,
  correctness, faithfulness, tool-selection accuracy, hallucination, multi-turn goal-success),
  failure/root-cause detectors, red-teaming/attack simulation, and a CLI — a full pre/post-
  deployment quality framework rather than a debugging afterthought.
- **Deployment targets span AWS and non-AWS**: documented one-line deploy guides for Bedrock
  AgentCore, AWS Lambda, Fargate, App Runner, EKS, EC2, Docker, Kubernetes, and Terraform/Nx
  IaC — AgentCore is presented as one deployment option among several, not a required pairing.

### Amazon Bedrock AgentCore (managed runtime)

- **Framework- and model-agnostic hosting platform**: "an agentic platform for building,
  deploying, and operating highly effective agents securely at scale using any framework and
  foundation model" — works with Strands, LangGraph, CrewAI, LlamaIndex, Google ADK, OpenAI
  Agents SDK, or custom/no framework, and any of Bedrock, Anthropic direct, Google Gemini,
  OpenAI, Meta Llama, or Mistral. This is the direct AWS counterpart to Azure AI Foundry Agent
  Service and Vertex AI Agent Engine as a "bring your own agent, we host it" runtime.
- **Modular service family, not a monolith**: independently usable services include Runtime
  (hosting/execution), Harness (a managed single-API-call agent loop with its own
  microVM-isolated sessions), Memory (short/long-term, cross-agent-shareable), Gateway (turns
  APIs/Lambda/existing services into MCP-compatible tools, and connects to external MCP
  servers), Identity (agent auth compatible with existing IdPs — Cognito, Okta, Entra ID,
  Auth0), Code Interpreter and Browser (sandboxed execution tools), Observability
  (OTel-based), Evaluations, Optimization (AI-generated prompt/tool-description tuning with
  A/B testing), Policy (Cedar-based deterministic tool-call authorization), and Registry
  (org-wide catalog of agents/MCP servers/tools).
- **Session isolation is microVM-based**, matching Azure's per-session VM model: "each user
  session runs in a dedicated microVM with isolated CPU, memory, and filesystem resources...
  After session completion, the entire microVM is terminated and memory is sanitized" —
  architecturally analogous to Azure Foundry's per-session VM-isolated sandboxes
  (`azure-hosted-agents.md`) and functionally similar to Anthropic's on-demand "hands"
  abstraction (`anthropic-managed-agents.md`).
- **Two compute types for different workload shapes**: **microVMs** for fully managed,
  instant-start, scale-on-demand, pay-per-use sessions (default); **Instances** for
  AWS-managed EC2 infrastructure in the customer's own account, supporting persistent
  multi-day sessions, GPU acceleration, and multiple collaborating agents sharing one instance
  — a middle ground between ephemeral serverless and always-on infrastructure not called out
  this explicitly in the Azure or Anthropic notes.
- **Extended execution + persistent filesystem**: supports both real-time and long-running
  workloads up to 8 hours, with filesystem state (files, installed packages, build artifacts)
  surviving session stop/resume cycles — comparable to Azure Foundry's persistent
  `$HOME`/`/files` model (though the exact relationship between the 8-hour execution window and
  longer session/filesystem persistence limits wasn't fully reconciled in the docs reviewed and
  merits direct verification before being quoted precisely).
- **Consumption-based pricing**: charges only for resources actually consumed, "typically
  eliminating charges during I/O wait periods when agents are primarily waiting for LLM
  responses" — a more granular, CPU-active-time-based billing model than a flat per-session or
  per-replica charge, with no upfront commitments or minimum fees.
- **Identity mirrors Azure's per-deployment model but is IdP-agnostic**: Runtime, powered by
  AgentCore Identity, assigns distinct identities to agents and integrates with existing
  corporate IdPs (Okta, Entra ID, Cognito), plus supports outbound auth flows (OAuth or API
  keys) for agents to call third-party services on a user's behalf — a broader scope than
  Azure Foundry's Entra-ID-only, inbound-focused identity.
- **MCP and A2A both natively supported**, with dedicated docs for deploying MCP servers and
  A2A servers directly inside AgentCore Runtime, plus an "AG-UI" server deployment path (a
  protocol not mentioned in the Azure or Anthropic notes, worth a follow-up).
- **Observability feeds a closed-loop Evaluations/Optimization pipeline**: OTel-standardized
  output ("any monitoring stack that integrates with standardized OpenTelemetry-compatible
  format") directly feeds automated Evaluations (agent/tool-call assessment on captured
  traces) and Optimization (AI-generated prompt/tool-description changes validated via A/B
  testing through Gateway traffic-splitting) — an "observe → evaluate → auto-tune" pipeline
  not described in the Azure or Anthropic managed-agent notes.
- **Gateway + Policy is the tool-integration and authorization layer**: Gateway converts APIs,
  Lambda functions, and enterprise services (Salesforce, Zoom, JIRA, Slack) into
  MCP-compatible tools "with just a few lines of code" and proxies to pre-existing external
  MCP servers; Policy intercepts and authorizes every tool call before execution via Cedar
  policy language or natural-language rules — a first-class, platform-level authorization gate
  rather than an application-level concern.
- **"Harness" is a distinct sub-service, separate from Runtime**: Harness is a higher-level
  managed agent loop (single API call, model+prompt+tools inline — closer to a hosted
  "Strands-lite"), while Runtime is the generic, framework-agnostic hosting layer most directly
  comparable to Azure Foundry's/Vertex Agent Engine's hosting model. Both use microVM session
  isolation but serve different levels of abstraction.

## CF relevance

AgentCore reinforces the pattern already seen in Azure Foundry and Anthropic's managed-agents
architecture — VM/microVM session isolation, per-agent/per-session identity, and
OTel-standardized observability as baseline expectations for hosting untrusted or
semi-trusted agent code — but adds two elements not as explicit in the other two vendor notes:
(1) a tool-integration gateway with per-call authorization (Gateway + Policy/Cedar) as a
first-class platform service rather than an application concern, and (2) a closed
observability→evaluation→optimization loop treating agent quality tuning as a platform-level
capability. Both are worth flagging as open design questions for a CF-native agent runtime:
should tool-call authorization and prompt/tool optimization live at the platform layer, or
stay entirely within the application, as CF's stateless-process model would otherwise assume?
Strands Agents itself — a lightweight, multi-provider, Apache-2.0 SDK with strong MCP/A2A
support and no hard AWS dependency — is a plausible reference implementation to prototype
against if CF explores agent-framework support independent of any single cloud vendor.

## Open questions

- Should tool-call authorization (AgentCore's Gateway + Policy model) be a platform-level
  primitive on CF, similar to how service bindings scope credential access today, or remain an
  application-level library concern?
- Is the "observe → evaluate → auto-tune" closed loop (Observability feeding Evaluations and
  Optimization) something CF should consider as a platform capability, or is that inherently
  vendor/model-specific and out of scope for a platform?
- AgentCore's two compute types (ephemeral microVMs vs. persistent EC2-backed Instances) map
  onto a familiar CF tension between scale-to-zero ephemeral workloads and long-lived stateful
  processes — does CF's existing Diego cell model already support both shapes, or would a new
  primitive be needed?
- Strands' explicit non-support of A2A in Swarm mode (only Graph/tool-based patterns) suggests
  A2A integration maturity varies even within one framework's own orchestration modes — is
  this a signal that A2A adoption will remain uneven across multi-agent patterns generally,
  something CF should account for when picking an interop baseline?
