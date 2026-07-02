---
title: "OpenTelemetry Semantic Conventions for GenAI"
author: Ruben Koster (@rkoster)
date: 2026-07-02
tags: [observability-governance, ecosystem-survey]
cf_areas: [loggregator]
status: draft
sources:
  - https://opentelemetry.io/docs/specs/semconv/gen-ai/
---

## Summary

OpenTelemetry defines semantic conventions for generative AI operations (currently in
Development status) covering all four OTel signals. The conventions standardize span
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
  `gen_ai.client.response.status`.
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
