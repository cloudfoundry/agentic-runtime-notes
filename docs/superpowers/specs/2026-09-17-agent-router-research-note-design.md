# Agent Router Research Note Design

## Goal

Add a sourced research note on Agent Router, formerly Envoy AI Gateway, to help the
Cloud Foundry agent-runtime research group understand its architecture and relevance.

## Scope

The note will describe documented behavior from the Agent Router repository and
documentation, then clearly separate Cloud Foundry analysis from upstream facts. It will
cover:

- The OpenAI-compatible API and Agent Router's role as an AI traffic control plane.
- The Kubernetes control plane: Agent Router controller, Envoy Gateway controller,
  Kubernetes API, CRDs, and xDS configuration.
- The data plane: Envoy Proxy, AI Gateway External Processor, provider adapters, response
  normalization, credentials, and token-based rate limiting.
- The relationship between `AIGatewayRoute`, `AIServiceBackend`, and
  `BackendSecurityPolicy`.
- Standalone `aigw run` and Kubernetes deployment modes.
- Cloud Foundry relevance, including a shared AI gateway service, service bindings and
  secret management, routing and policy enforcement, observability, and the implications
  of Agent Router's Kubernetes-specific control plane.

## Structure

Create `research/agent-router.md` using the repository template and required sections:

1. Summary
2. Key findings
3. CF relevance
4. Open questions

The frontmatter will include the author, current date, relevant tags, `status: draft`,
primary upstream sources, and provisional ratings with concise justifications.

## Sources and evidence

Use the Agent Router GitHub repository README, Apache 2.0 license, concepts documentation,
system architecture, control-plane, data-plane, resources, getting-started, and CLI pages.
Claims about Cloud Foundry will be framed as analysis or open questions rather than
presented as Agent Router capabilities.

## Validation

Run the repository's note validation and test suite. Confirm that the new file has valid
frontmatter, a kebab-case filename, all required sections, linked sources, no template
placeholders, and only the intended tracked changes are committed.
