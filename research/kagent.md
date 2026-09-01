---
title: "kagent — Kubernetes-Native Framework for Operations-Focused AI Agents"
author: Ruben Koster (@rkoster)
date: 2026-08-10
tags: [orchestration, inter-agent-comms, observability-governance, runtime-lifecycle, ecosystem-survey]
cf_areas: []
status: draft
sources:
  - https://github.com/kagent-dev/kagent
  - https://kagent.dev/docs/kagent/getting-started/quickstart
  - https://kagent.dev/docs/kagent/concepts/agents
---

## Summary

[kagent](https://github.com/kagent-dev/kagent) is a CNCF, Kubernetes-native framework for
building, deploying, and managing AI agents as first-class Kubernetes custom resources
(`Agent`, `ModelConfig`, `ToolServer`), managed with regular `kubectl`/Helm workflows. Unlike
the general-purpose agent SDKs covered elsewhere in this research (MAF, Dapr Agents), kagent
ships pre-built with an operations/platform-engineering toolset — bundled MCP servers for
Kubernetes, Istio, Helm, Argo, Prometheus, Grafana, and Cilium — making its default use case
"AI agent that operates your cluster and its adjacent infrastructure" rather than a
general-purpose agent-building SDK.

## Key findings

- **Four core components**: a **Controller** (Kubernetes controller reconciling
  `Agent`/`ModelConfig`/`ToolServer` custom resources into running agents), a web **UI**
  (agent/tool management dashboard, `kagent dashboard`), an **Engine** (executes agents,
  built on Google's [Agent Development Kit](https://google.github.io/adk-docs/) — ADK), and a
  **CLI** (`kagent install`, `kagent dashboard`, etc.). Everything is declarative YAML managed
  the same way as any other Kubernetes workload.
- **Ops-focused built-in toolset**: kagent ships an MCP server bundling tools for Kubernetes,
  Istio, Helm, Argo, Prometheus, Grafana, and Cilium out of the box — clearly aimed at
  platform/SRE use cases (cluster troubleshooting, service-mesh config, GitOps, metrics
  querying) rather than generic chatbot/RAG agents. All tools are exposed as `ToolServer`
  custom resources, shareable across multiple `Agent` resources.
- **Dual agent runtime, a real cold-start/footprint trade-off**: declarative agents can run
  on either a **Python** ADK runtime (default; ~15s startup; full access to Google ADK,
  LangGraph, CrewAI framework integrations) or a **Go** ADK runtime (~2s startup; lower
  memory; native implementation; still supports MCP, memory, and human-in-the-loop). This is
  an explicit, documented engineering trade-off between ecosystem breadth and
  autoscaling/cold-start performance — relevant to any scale-to-zero agent deployment model
  (see `keda.md`).
- **Agents-as-tools (hierarchical delegation)**: any `Agent` can be referenced as a tool by
  another `Agent` — same-namespace or cross-namespace — enabling composition (e.g. a
  general troubleshooting agent delegating PromQL-query construction to a dedicated
  `promql-agent`). This is kagent's native multi-agent orchestration pattern, expressed as
  ordinary Kubernetes resource references rather than a custom workflow-graph DSL.
- **A2A support, auto-bridged to MCP**: kagent agents can be A2A-enabled (see `a2a-protocol.md`
  for the protocol), and any A2A-enabled agent is *automatically* also exposed as an MCP
  server on the same controller endpoint (default port 8083, `/mcp` path) — i.e. one agent
  definition is simultaneously consumable via both A2A (agent-to-agent delegation) and MCP
  (tool-style invocation) without separate configuration.
- **Provider-agnostic and observable by design**: `ModelConfig` resources abstract over
  OpenAI, Azure OpenAI, Anthropic, Google Vertex AI, Ollama, and custom/gateway-routed models.
  Built-in OpenTelemetry tracing is a first-class, documented feature (see
  `opentelemetry-genai.md` for the semantic-convention angle this note doesn't independently
  verify).
- **Prompt composition via ConfigMaps**: system prompts support Go `text/template` includes
  (`{{include "alias/key"}}`) resolved from ConfigMaps at reconciliation time, so common
  safety/tool-usage boilerplate can be centralized and reused across many agents rather than
  duplicated per-agent — a small but concrete "platform provides shared guardrails" pattern.

## CF relevance

kagent is the closest thing in this research set to "an AI agent whose job is to operate a
platform," which maps directly onto the use case flagged for this note: assisting CF operators
(diagnosing failed deployments, querying BOSH/Diego state, correlating logs and metrics,
suggesting remediations) the same way kagent assists Kubernetes/Istio operators today. Its
architecture — CRD-based agent definitions, a bundled ops-tool MCP server, and agents-as-tools
composition — is a plausible template for a "CF operator agent" that ships with tools for `cf`
CLI operations, Diego/BOSH introspection, and log/metrics querying, exposed the same way kagent
exposes cluster tools. The Go-vs-Python runtime trade-off is also a useful, concrete data point
for CF's own autoscaling/cold-start discussions (see `keda.md`) independent of the Kubernetes
specifics.

## Open questions

- Kagent's tool model assumes a Kubernetes control plane to reconcile against — how much of
  its architecture (CRD-based agent definition, ToolServer sharing, agents-as-tools) is
  actually Kubernetes-specific vs. portable to a non-k8s control plane like Diego/BOSH?
- Would a CF-native equivalent make more sense as "teach kagent to speak CF" (new ToolServer
  MCP tools for `cf`/BOSH/Diego) or as a from-scratch CF-native agent operator inspired by the
  same architecture? What would reusing kagent directly cost vs. buy?
- How mature is the human-in-the-loop (HITL) support mentioned in the runtime comparison table
  — is it a confirmation gate before mutating actions (e.g. before `kubectl delete`-equivalent
  tool calls), and would that generalize to gating destructive CF operator actions?
- Kagent bridges A2A and MCP automatically for the same agent — is this a pattern other
  frameworks in this research set (MAF, Dapr Agents) should adopt, or does conflating "agent
  as A2A peer" and "agent as MCP tool" have downsides (e.g. unclear capability boundaries)?
- How does kagent's CNCF governance and roadmap maturity compare to the other, more
  vendor-driven frameworks in this research set (MAF/Microsoft, Dapr Agents/Diagrid) — does
  vendor-neutral governance change the calculus for CF adopting or integrating with it?
