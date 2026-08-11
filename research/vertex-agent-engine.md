---
title: "Vertex AI Agent Engine (Gemini Enterprise Agent Platform) — Google's Managed Agent Runtime"
author: Ruben Koster (@rkoster)
date: 2026-08-10
tags: [runtime-lifecycle, identity, observability-governance, sandboxing-isolation, ecosystem-survey]
cf_areas: []
status: draft
sources:
  - https://cloud.google.com/gemini-enterprise-agent-platform/build/runtime
  - https://cloud.google.com/gemini-enterprise-agent-platform/scale/runtime/agent-identity
  - https://cloud.google.com/gemini-enterprise-agent-platform/scale/sandbox
  - https://cloud.google.com/gemini-enterprise-agent-platform/scale/memory-bank
  - https://cloud.google.com/gemini-enterprise-agent-platform/govern/gateways/agent-gateway-overview
  - https://cloud.google.com/gemini-enterprise-agent-platform/scale/runtime/tracing
  - https://cloud.google.com/gemini-enterprise-agent-platform/optimize/evaluation/agent-evaluation
  - https://cloud.google.com/gemini-enterprise-agent-platform/agents
---

## Summary

Google's **Vertex AI Agent Engine** — recently rebranded under the **Gemini Enterprise Agent
Platform**, with the managed runtime component now called **Agent Runtime** (API resource
name still `ReasoningEngine` for backward compatibility) — is a fully managed,
framework-agnostic runtime for deploying, scaling, and operating AI agents on Google Cloud.
It is the deployment target for Google ADK agents (`google-adk.md`) but also supports
LangChain, LangGraph, AG2 (AutoGen), LlamaIndex, and A2A-protocol agents. This is the direct
Google counterpart to Azure AI Foundry Agent Service (`azure-hosted-agents.md`) and AWS
Bedrock AgentCore (`aws-agents.md`), completing the four-way managed-hosting comparison
alongside Anthropic's managed agents (`anthropic-managed-agents.md`). Around the runtime,
Google has built a "Build → Scale → Govern → Optimize" lifecycle: Sessions and Memory Bank
for context management, Sandboxes for untrusted code/computer-use execution, SPIFFE-based
Agent Identity, an Agent Gateway for tool/network policy enforcement, and Cloud
Trace/OpenTelemetry observability feeding a Gen AI Evaluation Service — a shape that closely
parallels AWS AgentCore's Gateway/Policy → Identity → Memory → Observability →
Evaluation/Optimization pipeline.

## Key findings

- **Agent Runtime is the deployment target for ADK, but framework-agnostic**: ADK gets "full
  integration" (features work across framework, runtime, and the wider GCP ecosystem);
  LangChain/LangGraph/AG2/LlamaIndex get "Agent Platform SDK integration" (managed templates);
  CrewAI and other custom frameworks require adapting a "custom template" via the runtime
  contract. A2A agents are also natively deployable (preview).
- **Isolation is at the container/sandbox layer, not a per-session VM/microVM layer**: Agent
  Runtime itself is "a trusted environment that executes your code and manages the agent's
  lifecycle" — closer to a regular managed container service than to Azure's per-session VM or
  AWS AgentCore's per-session microVM. Untrusted work (code execution, browser "computer use")
  is explicitly pushed to a separate **Sandbox** resource using "secure container sandboxing"
  — Google's docs stop short of specifying gVisor/Kata/microVM internals the way AWS documents
  Firecracker (see `firecracker-microvm.md`). This is a materially different isolation posture:
  Google separates "trusted runtime" from "untrusted sandbox" rather than isolating every
  session in its own VM.
- **Memory Bank — managed, LLM-driven long-term memory, contrasted with static RAG**: extracts,
  consolidates, and evolves "memories" (facts) from conversation history, scoped per identity
  (agent + user), with similarity-search retrieval, automatic TTL expiration, and full
  memory-revision history. Unlike RAG's static external corpus, Memory Bank continuously
  integrates new agent-provided context. Google explicitly flags **prompt injection / memory
  poisoning** as a first-class risk and recommends Model Armor, red-teaming, and sandboxed
  execution as mitigations — a security concern about persistent agent memory named directly
  here more than in the Azure/Anthropic/AWS notes.
- **Agent Identity: SPIFFE-based per-agent principals, not plain service accounts** — a close
  analog to AWS AgentCore's per-agent identity and Azure's per-deployment Entra ID. Each
  deployed agent can get a unique identity (`principal://TRUST_DOMAIN/NAMESPACE/AGENT_NAME`),
  auto-provisioned with an x.509 certificate, secured by default via a Context-Aware Access
  (CAA) policy enforcing **mTLS-bound, certificate-bound tokens** — tokens are cryptographically
  bound to the originating runtime and become un-replayable if stolen, directly mitigating
  credential-theft attacks (a different mitigation strategy than Anthropic's "remote hands"
  architecture, which never hands out credentials at all, `anthropic-managed-agents.md`). IAM
  allow/deny and Principal Access Boundary policies can target individual agents or all agents
  in a project/org. Without explicit agent-identity opt-in, agents fall back to conventional
  service accounts.
- **Agent Gateway — the tool/network authorization layer, directly analogous to AWS
  AgentCore's Gateway+Policy pair**: mediates Client-to-Agent (ingress) and Agent-to-Anywhere
  (egress, e.g. agent → MCP server) traffic, enforcing IAM (via Identity-Aware Proxy) as the
  default authorization layer, with optional delegation to Model Armor (prompt-injection/
  data-leakage inspection) and Semantic Governance Policies (context-aware "toxic tool
  combination" protections). It's protocol-aware for MCP (can parse MCP request attributes for
  fine-grained per-tool policy) and passes through A2A/REST/gRPC. Does not support VPC Service
  Controls, and caps at 5,000 registered resources per gateway instance.
- **Tool integration**: function calling with Gemini models, an "Agent Registry" of approved
  agents/tools (including third-party MCP servers) that Agent Gateway consults for
  authorization, and both first-party and BYO MCP server connectivity.
- **Observability is Cloud Trace + OpenTelemetry using the emerging GenAI semantic
  conventions** — directly comparable to Azure Foundry's auto-injected OTel/App Insights and
  AWS AgentCore's Observability service (see `opentelemetry-genai.md`). Enabling tracing is
  env-var driven for ADK agents, or an `enable_tracing=True` SDK flag for
  LangChain/LangGraph/LlamaIndex agents; custom agents instrument OTel manually. Spans follow
  OpenTelemetry's GenAI semantic conventions, explicitly flagged experimental/unstable.
- **Deployment/scaling is serverless/consumption-based with a free tier**: "fully managed...
  deploy and scale agents... without the need to manage underlying infrastructure." No
  explicit cold-start numbers or scale-to-zero details surfaced in the docs reviewed (unlike
  Azure's documented 15-minute idle timeout / 30-day max session) — Agent Runtime is
  positioned as serverless with usage-based pricing plus a free tier. Terraform-based
  provisioning and an "Agents CLI" (scaffold/evaluate/deploy/publish/observe lifecycle with
  Cloud Build CI/CD) support production rollout, including revision/traffic management.
- **A2A protocol support is native but explicitly marked preview**: Agent Runtime supports
  building/deploying A2A agents so they "communicate and collaborate with other agents
  regardless of framework," and Agent Gateway passes through A2A traffic alongside
  MCP/REST/gRPC. Agent identity's IAM model also covers authorizing calls to other
  A2A-hosted agents.
- **Evaluation is a structured, iterative lifecycle service feeding an optimization loop** —
  the Google counterpart to AWS AgentCore's Observability → Evaluation/Optimization pipeline
  (and building on the ADK Eval tooling covered in `google-adk.md`). The flow: define eval
  cases → run inference (with optional user simulation) → capture immutable traces → compute
  reference-based or reference-free metrics (LLM-as-judge autoraters) → analyze failure
  clusters → auto-propose and verify prompt/tool optimizations. An "Example Store" (few-shot
  example management) feeds the same continuous-improvement flywheel.
- **Enterprise security controls are inconsistent across services**: VPC Service Controls,
  CMEK, data-residency, and HIPAA are supported for Agent Runtime, Sessions, Memory Bank, and
  Code Execution, but **not** for Example Store; Access Transparency/Access Approval are
  supported for Runtime/Sessions/Memory Bank but not Evaluation, Example Store, or Code
  Execution. Memory Bank's ML processing occurs in the region of the configured model
  endpoint — a data-residency nuance worth flagging for regulated workloads.

## CF relevance

Vertex AI Agent Engine completes a four-way pattern now visible across Azure, Anthropic, AWS,
and Google's managed agent-hosting offerings: per-agent/per-session identity, OTel-standardized
observability, and a tool-integration gateway with policy-based authorization are converging
as baseline expectations for any vendor hosting third-party or semi-trusted agent code — useful
validation for CF's own agent-runtime design even where CF doesn't adopt any of these vendors
directly. Google's choice to separate "trusted runtime" from "untrusted sandbox" (rather than
isolating every session in its own VM/microVM) is architecturally distinct from Azure and AWS
and worth comparing directly against CF's existing app/process trust model — it may be a closer
conceptual fit for a platform like CF that already assumes a baseline of trusted app-instance
isolation (Diego cells) and layers additional sandboxing only for genuinely untrusted
operations. The observability → evaluation → optimization closed loop (also seen in AWS
AgentCore) reinforces the open question raised in `aws-agents.md`: should CF treat this as a
platform-level capability, or leave it entirely to application/vendor tooling?

## Open questions

- Google's "trusted runtime + separate untrusted sandbox" split is architecturally closer to
  CF's existing app-instance model than Azure's/AWS's "isolate every session" approach — is
  this the more natural starting point for a CF-native agent runtime design, given CF already
  has a trusted-process isolation baseline (Diego)?
- Is SPIFFE-based, certificate-bound agent identity (mitigating credential replay even if
  stolen) a stronger baseline than CF's current app-instance identity model — worth evaluating
  independent of any Google Cloud adoption?
- How would CF reconcile the inconsistent enterprise-security-control coverage seen across
  Google's own services (VPC-SC/CMEK supported for some agent services but not others) — is
  this a cautionary example of a modular-services architecture creating governance gaps that
  CF should specifically design against?
- Given Google's Evaluation service builds directly on ADK's built-in eval tooling
  (`google-adk.md`), is there a reusable "framework ships eval hooks, platform provides the
  evaluation service" pattern CF could adopt regardless of which agent framework a workload
  uses?
