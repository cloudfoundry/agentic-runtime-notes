# Agentic Identity Broker Research Note Design

## Goal

Add a sourced research note on Agentic Identity Broker as delegated OAuth and credential
mediation infrastructure for AI agents.

## Scope

The note will cover the broker's principals, agents, services, permission sets, grants, user
sessions, consent UI, dual-port architecture, trusted proxy boundary, encrypted token vault,
RFC 8693 token exchange, optional Envoy ExtProc sidecar, and audit identities. It will explain
why agents should not receive long-lived third-party provider credentials.

The Cloud Foundry analysis will map the broker to UAA, instance identity, service bindings,
agent/tool authorization, service brokers, credential rotation, and Loggregator/audit. It will
not claim existing CF integration.

## Structure and evidence

Create `research/agentic-identity-broker.md` with the required four sections and frontmatter.
Use the official website concepts, architecture, delegation, token exchange, encryption, and API
documentation. Clearly distinguish authentication at the trusted edge from authorization and
credential mediation inside the broker.

## Validation

Run Devbox validation and tests, inspect whitespace/staged files, commit the note and plan on
`research/agentic-identity-broker`, push, and open a PR targeting `main` without unrelated
artifacts.
