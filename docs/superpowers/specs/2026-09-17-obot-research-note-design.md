# Obot Research Note Design

## Goal

Add a sourced research note on Obot as a governed AI platform combining gateways, registries,
hosted sandboxes, identity, policy, and audit.

## Scope

The note will describe Obot's MCP and LLM gateways, hosted MCP servers and agents, skills and
MCP registries, identity and credential management, access policies, request filtering, and
correlated audit logs. It will distinguish user-device components such as Sentry and the CLI
from Obot Server capabilities.

The Cloud Foundry analysis will map these capabilities to shared platform services, service
bindings, Diego-hosted workloads, sandbox/isolation requirements, CAPI lifecycle management,
and Loggregator-compatible auditing. It will not claim existing CF integration.

## Structure

Create `research/obot.md` using the repository template and required sections:

1. Summary
2. Key findings
3. CF relevance
4. Open questions

Use provisional ratings and clearly label deployment and CF mapping conclusions as analysis.

## Sources and evidence

Use the Obot GitHub repository, README, architecture image/documentation, and deployment or
feature documentation available from the project. Claims about Cloud Foundry will be analysis
or open questions, not documented Obot integrations.

## Validation

Run the repository's configured Devbox validation and test scripts, inspect whitespace and the
staged diff, then commit the note, plan, and design spec on `research/obot`. Push the branch and
open a new PR targeting `main` without staging unrelated environment artifacts.
