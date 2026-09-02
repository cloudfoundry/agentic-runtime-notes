---
title: "Heroku AI — Managed Inference, Agents, and MCP on a Buildpack-Era PaaS"
author: Ruben Koster (@rkoster)
date: 2026-08-24
tags: [runtime-lifecycle, sandboxing-isolation, inter-agent-comms, ecosystem-survey, observability-governance, identity]
cf_areas: [buildpacks, capi, diego]
status: draft
sources:
  - https://www.heroku.com/ai/
  - https://www.heroku.com/blog/heroku-ai-studio-workspace-for-smarter-faster-ai-apps/
  - https://devcenter.heroku.com/categories/ai-integrations
  - https://www.heroku.com/blog/accelerating-ai-dev-new-models-performance-improvements-messages-api/
  - https://www.heroku.com/blog/code-execution-sandbox-for-agents-on-heroku/
  - https://www.heroku.com/ai/mcp-on-heroku/
  - https://github.com/heroku/mcp-code-exec-python
ratings:
  platform-impact:
    value: 78
    note: 'Initial review of Heroku AI — Managed Inference, Agents, and MCP on a Buildpack-Era PaaS: its subject and tags indicate how broadly the capability could affect an agentic platform.'
  maturity:
    value: 76
    note: 'Initial review of Heroku AI — Managed Inference, Agents, and MCP on a Buildpack-Era PaaS: this score reflects the amount of established external practice visible in the note.'
  novelty:
    value: 62
    note: 'Initial review of Heroku AI — Managed Inference, Agents, and MCP on a Buildpack-Era PaaS: this score reflects how distinct or emerging the approach appears in the current landscape.'
  actionability:
    value: 66
    note: 'Initial review of Heroku AI — Managed Inference, Agents, and MCP on a Buildpack-Era PaaS: this score reflects how readily the material could guide a focused experiment or follow-up.'

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
  reachable directly from the add-on. It's dev-tooling, not a runtime change.
- **Sandboxing reuses an existing primitive — one-off dynos**: Heroku ships a "Code
  Execution Sandbox for Agents" (launched alongside the inference add-on, May 2025) that
  runs untrusted LLM-generated code inside **one-off dynos** — the decade-old mechanism
  behind `heroku run` — spun up on demand and terminated after use. No new sandbox runtime
  was built; isolation is achieved by reusing the ephemeral-container lifecycle Heroku
  already had, so blast radius is bounded to one throwaway container per invocation.
  Exposed two ways: as built-in tools (`code_exec_python/ruby/node/go`) in the Managed
  Inference and Agents API (`v1/agents/heroku`), and as open-source MCP servers
  (e.g. `heroku/mcp-code-exec-python`) any MCP client can attach to. This implements
  Anthropic's "programmatic tool calling" pattern — the model writes code that loops/filters
  server-side and only a summary re-enters the model's context, which Heroku cites as
  cutting token consumption ~37% on average (up to 98% in some cases). A `max_calls`
  runtime param bounds sandbox invocations per agent loop.
- **Sandbox dependency resolution happens live, per call, with no offline path**: reading
  the open-source `heroku/mcp-code-exec-python` implementation shows two separate layers.
  The Python *interpreter* version is fixed at deploy time by the buildpack (a
  `.python-version` file pins it into the slug every one-off dyno boots from). Requested
  *libraries*, however, are resolved at request time: the `code_exec_python` tool accepts
  an optional `packages` list, and on each call the server creates a throwaway venv inside
  the dyno, runs `pip install <packages>` against the public PyPI index, executes the code,
  then deletes the venv. The implementation's own docstring notes this "does NOT mean the
  code is fully isolated or secure — it just means the package installations are isolated";
  the dyno container boundary is what actually isolates execution. This design requires
  live egress to a public package index at execution time, with no documented offline
  buildpack/mirror path and no caching or version pinning across calls — every invocation
  re-resolves and re-downloads from scratch.
- **No durable-execution primitive found**: nothing in the surveyed material describes
  workflow-style checkpointing, replay, or resumable agent state across steps/restarts (the
  kind of thing Temporal/Restate provide). Sandboxes are stateless and ephemeral — state
  dies with the one-off dyno — and inference calls are plain stateless request/response.
  Any multi-step agent loop that must survive beyond a single request/dyno is left to the
  app developer to persist itself (e.g., in Postgres). This is a notable contrast with
  Azure Foundry's per-session VM model, which offers a persistent filesystem and 30-day
  resumable sessions (`azure-hosted-agents.md`).
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

The sandbox design is directly portable: Heroku's "reuse an existing ephemeral-compute
primitive for untrusted code execution" maps almost one-to-one onto CF's task model —
Diego one-off tasks are CF's equivalent of one-off dynos, and a "code execution sandbox"
add-on could plausibly be built as a broker that runs agent-submitted code as a short-lived
Diego task rather than requiring a new isolation layer. However, Heroku's dependency
resolution (live `pip install` per call against a public package index) assumes
always-on internet egress from the sandbox — a pattern that doesn't fit enterprise CF
deployments that typically run offline/mirrored buildpacks with no direct app egress. CF's
existing staging/droplet split (resolve dependencies once at `cf push` time, run app
instances from the resulting immutable droplet) is a different model that might be a
better fit for offline environments, but would need its own design (see
`ideas/staged-sandbox-environments.md`). Separately, the absence of any durable-execution
story on Heroku means CF gets no free lunch there either — a resumable, checkpointed
agent-loop primitive (if the working group decides it's needed) would be new ground for
both platforms, not something to crib from Heroku's design.

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
- Could a "code execution sandbox for agents" be implemented on CF today as a broker that
  dispatches agent-submitted code to a short-lived Diego task, mirroring Heroku's
  one-off-dyno approach — or does untrusted-code execution need stronger isolation
  (gVisor/Kata, a dedicated runc profile) than a standard Diego cell provides?
- Heroku resolves sandbox dependencies live per call against public PyPI, with no offline
  or caching path. Could CF instead reuse its existing staging/droplet mechanism — resolve
  a dependency manifest once into a cacheable droplet, then execute against an
  already-staged environment — to support offline/mirrored-buildpack deployments and avoid
  re-resolving dependencies on every sandbox invocation? (see
  `ideas/staged-sandbox-environments.md`)
- Neither Heroku nor (per the earlier Azure/other notes) most surveyed platforms offer true
  durable execution for agent loops. Is this a genuine gap the working group should design
  for, or is "persist state yourself in a bound service" (Heroku's implicit answer) good
  enough for CF's Phase 1 scope?
