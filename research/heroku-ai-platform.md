---
title: "Heroku AI — Managed Inference, Agents, and MCP on a Buildpack-Era PaaS"
author: Ruben Koster (@rkoster)
date: 2026-08-24
tags: [runtime-lifecycle, inter-agent-comms, ecosystem-survey, observability-governance, identity]
cf_areas: [buildpacks, capi]
status: draft
sources:
  - https://www.heroku.com/ai/
  - https://www.heroku.com/blog/heroku-ai-studio-workspace-for-smarter-faster-ai-apps/
  - https://devcenter.heroku.com/categories/ai-integrations
  - https://www.heroku.com/blog/accelerating-ai-dev-new-models-performance-improvements-messages-api/
---

## Summary

Heroku — the platform whose buildpack concept Cloud Foundry adopted and co-evolved with —
is repositioning itself as an "AI PaaS." It layers a managed inference/agents add-on, an
MCP tool-gateway, pgvector-backed vector search, and an interactive prompt-tuning workspace
(AI Studio) on top of its existing dyno/add-on model, rather than introducing a new agent
runtime primitive. Apps keep their normal dyno lifecycle; AI capability is delivered as
attached add-ons and API endpoints (OpenAI- and Anthropic-compatible) that any language
buildpack can consume via environment-variable config.

## Key findings

- **AI-as-add-on, not new compute primitive**: "Heroku Managed Inference and Agents" is
  delivered as a standard add-on (`heroku-inference`), attached like Postgres or Redis. It
  injects `INFERENCE_URL` / `INFERENCE_KEY` / `INFERENCE_MODEL` config vars into the dyno's
  environment — the same attach-and-inject pattern used for every other Heroku add-on. No
  new dyno type or process model was introduced for agent workloads.
- **API compatibility over new protocols**: Inference is exposed via an OpenAI-compatible
  Chat Completions surface plus a newer Anthropic-compatible `v1/messages` endpoint
  (currently in preview, Anthropic models only). This lets existing SDKs (OpenAI, Anthropic,
  LangChain, LlamaIndex, Vercel AI SDK, Pydantic AI, LiteLLM) "just work" against
  Heroku-hosted models with a base-URL swap — echoed directly by a customer quote in the
  marketing page ("it uses the OpenAI APIs, so all the existing SDKs just work").
- **MCP as the tool/agent-interop layer**: "MCP Toolkits" provide a managed gateway to run
  and expose multiple MCP servers, giving both Heroku-hosted agents and external clients
  (Claude Desktop, Cursor) one consistent interface to call internal or external tools.
  This is Heroku's answer to inter-agent/tool-comms standardization — comparable in spirit
  to A2A adoption elsewhere (see `a2a-protocol.md`).
- **Vector search reuses the existing data service**: RAG/embeddings use `pgvector` on
  Heroku Postgres rather than a new managed vector DB product — extending an existing
  data-service instead of adding infrastructure surface area.
- **AI Studio = interactive workspace bolted onto the add-on**: A hosted UI
  (`aistudio.heroku.com`) for live prompt/tool iteration against provisioned models,
  reachable directly from the add-on. It's dev-tooling, not a runtime change — no isolated
  execution sandbox described, unlike Azure Foundry's per-session VM model
  (`azure-hosted-agents.md`).
- **Fast-moving model catalog with lifecycle policy**: Regular catalog churn (Claude Opus
  4.5 / Sonnet 4.5 / Haiku 4.5, Amazon Nova 2, Kimi K2 Thinking, MiniMax M2, Qwen3) with
  published deprecation dates (e.g., Claude 3 family retiring Jan 30 2026) and a
  stated goal of automatic fallback to a successor model on deprecation — an operational
  concern platforms will need to own as "model EOL" becomes analogous to stack/runtime EOL.
- **Data governance framed explicitly**: Open-weight models are stated to run on
  Heroku/AWS-controlled compute with neither Heroku nor the model provider retaining access
  to customer data or using it for training — a claim made prominently in the same breath as
  performance features, suggesting this is a purchase-decision driver for enterprise AI
  workloads.
- **Prompt caching as a default optimization**: System prompts and tool/function
  definitions are cached automatically to cut repeated-request latency (opt-out via an HTTP
  header); user messages/history are explicitly excluded from caching for privacy. This is a
  concrete example of a platform absorbing an agent-specific performance concern (repeated
  large tool-schema payloads) rather than leaving it to app code.

## CF relevance

Heroku's approach validates a "no new primitive" path: treat AI inference/agents/tools as
attachable services behind standard interfaces, and let the existing buildpack/app/dyno
model carry the workload unchanged. For Cloud Foundry — which inherited the buildpack
concept from this same lineage — this suggests an achievable near-term model: an
AI-service-broker (OSBAPI) pattern exposing OpenAI/Anthropic-compatible endpoints and an
MCP gateway, with credentials injected via `VCAP_SERVICES`, rather than inventing a new
agent-runtime abstraction. It also surfaces adjacent platform concerns CF doesn't yet
address: model lifecycle/deprecation policy as a first-class platform signal, and
prompt/tool-schema caching as a routing-layer optimization for agentic traffic patterns.

## Open questions

- Would an OSBAPI service broker exposing an OpenAI/Anthropic-compatible endpoint plus
  MCP-gateway wiring be sufficient for CF to reach functional parity with Heroku's AI
  add-on, or does agent orchestration need a runtime-level primitive after all?
- How should a platform surface upstream model deprecation/EOL to app owners — is this
  analogous to stack deprecation notices, and could `cf` tooling reuse that mechanism?
- Is prompt/tool-definition caching something the platform's routing tier (Gorouter) could
  offer generically, or does it inherently belong to the inference provider?
- Heroku frames "no training on customer data" as a headline trust claim — should CF define
  a similar baseline expectation for any AI-service broker admitted into the marketplace?
- Does an MCP gateway belong at the platform layer (like Heroku's MCP Toolkits) or is it
  better left as an ordinary buildpack-deployed app, given CF's app-centric model?
