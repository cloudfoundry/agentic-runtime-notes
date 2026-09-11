---
title: Agent Failure Checkpointing
author: Arsalan Khan (@asalan316)
date: 2026-08-13
tags: [runtime-lifecycle, sandboxing-isolation]
ratings:
  platform-impact:
    value: 75
    note: 'CF restarts crashed apps but cannot restore agent memory, task outputs, queue position, or bound-service session state from a platform-managed checkpoint.'
  maturity:
    value: 50
    note: 'Framework checkpointers demonstrate credible persistence and resume mechanisms, but transparent platform restoration across agent memory, queues, outputs, and bound-service sessions has no implementation or operational evidence here.'
  novelty:
    value: 25
    note: 'The proposal adapts the established checkpoint/restart pattern to agent conversation state, tool outputs, and work queues rather than introducing a new durability architecture.'
  actionability:
    value: 50
    note: 'The manifest sketch and invoice recovery example define desired behavior, but checkpoint granularity, state boundaries, storage, and multi-tenant quotas still require substantial scoping.'

---

## The idea

CF supports automatic checkpointing of agent state at configurable points, enabling resume-from-failure for long-running agent tasks. Just as CF restarts crashed apps transparently, it should resume crashed agents from their last checkpoint.

## Why it might matter

LangGraph, Anthropic, and multiple frameworks emphasize persistence through failures as critical for production agents. Agent workloads are often multi-step (research, analysis, code generation, testing) and expensive to restart — both in compute cost and wall-clock time. A 30-minute agent task that fails at minute 25 shouldn't restart from scratch.

Platform-level checkpointing reduces application complexity (no custom state management), enables consistent recovery semantics across frameworks, and could integrate with the graduated lifecycle states (running → suspended → dehydrated) for cost optimization.

## Example: Invoice processing agent

A finance team deploys an autonomous agent app to CF that processes vendor invoices overnight:

```text
cf push invoice-agent -m 1G --health-check-type process
cf bind-service invoice-agent llm-provider
cf bind-service invoice-agent s3-documents
cf set-env invoice-agent CHECKPOINT_STRATEGY "per-task"
```

The agent processes 500 invoices autonomously. At invoice #387, LLM provider has outage:

```text
Invoice Processing Agent (deployed app, running autonomously)
├── Task: Process 500 pending invoices from S3 bucket
│
├── Invoice #1-386: extracted, validated, posted to ERP
│   ✓ checkpoint: {processed: 386, errors: 12, last_id: "INV-2026-0386"}
│
├── Invoice #387: fetch from S3, call LLM for extraction
│   ✗ CRASH — LLM provider 503 at 3:47am
│
│   --- CF detects crash, finds checkpoint ---
│   --- Restarts agent container, restores state ---
│
├── Resume from checkpoint (not invoice #1):
│   Invoice #387: retry extraction
│   ✓ checkpoint: {processed: 387, ...}
│
├── Invoice #388-500: continue processing
│   ✓ DONE — 4.2 hours total (not 8+ hours if restarted)
│
└── Result: 500 invoices processed, 18 flagged for review
```

**Without platform checkpointing**: Developer writes custom state persistence to Redis/Postgres, handles resume logic, manages partial failure states manually.

**With platform checkpointing**: Developer declares checkpoint strategy in manifest, CF handles persistence and resume transparently.

```yaml
# manifest.yml
applications:
- name: invoice-agent
  agent:
    checkpoint:
      strategy: per-task      # per-task | per-tool-call | explicit | time-based
      storage: platform       # platform-managed or bring-your-own
      retention: 7d
```

**Checkpoint contents** (platform-managed):
- Agent memory/conversation state
- Accumulated task outputs
- Position in work queue
- Bound service session state (where possible)

## What to research next

- What is the right checkpoint granularity — per tool call, per LLM response, configurable by application?
- How does checkpoint storage interact with multi-tenancy — per-org storage quotas?
- What state needs checkpointing — conversation history, tool outputs, environment state, or all three?

## Related

- [per-session-sandboxes](per-session-sandboxes.md) — graduated lifecycle states (running, suspended, dehydrated)
