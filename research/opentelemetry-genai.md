---
title: "OpenTelemetry Semantic Conventions for GenAI"
author: Ruben Koster (@rkoster)
date: 2026-07-02
tags: [observability-governance, ecosystem-survey]
cf_areas: [loggregator]
status: draft
sources:
  - https://github.com/open-telemetry/semantic-conventions-genai
ratings:
  platform-impact:
    value: 58
    note: 'CF already transports application telemetry through Loggregator, but lacks standard platform treatment for model, token, agent, tool, and MCP spans and metrics.'
  maturity:
    value: 48
    note: 'The conventions cover major model vendors, agent operations, MCP, spans, events, and metrics within OpenTelemetry, but the document explicitly records Development status rather than stable standardization.'
  novelty:
    value: 40
    note: 'Token usage, time-to-first-chunk, planning, and tool-call semantics adapt established tracing and metrics conventions to GenAI rather than introducing a new observability architecture.'
  actionability:
    value: 82
    note: 'CF can instrument one model-and-tool request with the named gen_ai attributes and metrics, propagate its trace through platform routing, and test Loggregator export without designing a new protocol.'

---

## Summary

OpenTelemetry defines semantic conventions for generative AI operations (currently in
Development status) covering spans, metrics, and events. The conventions standardize span
attributes for LLM model calls, agent framework operations (planning, tool selection),
structured request/response events, and GenAI-specific metrics such as token usage and
operation duration.

## Key findings

- **Model spans**: Standardized attributes — `gen_ai.request.model`, temperature,
  `max_tokens`, and `gen_ai.usage.*` token metrics.
- **Agent spans**: Conventions for agent framework operations above individual model calls —
  planning, tool selection, multi-step reasoning.
- **Events**: Request/response payloads and tool call inputs/results as structured OTel
  events.
- **GenAI metrics**: `gen_ai.client.token.usage`, `gen_ai.client.operation.duration`,
  `gen_ai.client.operation.time_to_first_chunk`.
- **MCP integration**: Semantic conventions also defined for Model Context Protocol
  operations.
- **Vendor coverage**: Conventions cover OpenAI, Anthropic, Azure AI Inference, and AWS
  Bedrock.

## CF relevance

Platforms already collecting OTel traces and metrics have a clear path to supporting GenAI
observability — the conventions plug into existing pipelines without new infrastructure. The
coverage gap is at the agent-framework layer: current conventions focus on model-level spans,
while multi-step agent operations (tool orchestration, planning loops) are still developing.
A platform surfacing agent workloads would need to decide how to correlate agent-level spans
with platform-level routing and request traces.

## Open questions

- How to correlate agent spans with platform-level routing traces (request IDs, trace
  propagation)?
- Should agent-span conventions be extended at the platform level, or left to frameworks?
- Can platform health checks be extended to include model connectivity and token-limit
  headroom?
