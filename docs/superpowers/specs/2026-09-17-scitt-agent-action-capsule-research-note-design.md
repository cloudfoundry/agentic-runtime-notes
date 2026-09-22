# SCITT Agent Action Capsule Research Note Design

## Goal

Add a sourced research note on using SCITT and the Agent Action Capsule profile to make agent
actions independently verifiable and auditable in Cloud Foundry environments.

## Scope

The note will explain SCITT's transparency-service architecture and distinguish it from the
Agent Action Capsule statement profile. It will cover digest-committed capsule identity, COSE
producer envelopes, chains, verdicts including refusals, Class-1 and envelope/receipt
verification, and the current Internet-Draft governance status.

The Cloud Foundry analysis will consider instance identity certificates, UAA/CAPI/Diego event
correlation, authorization evidence, Loggregator integration, receipt storage, privacy, and
non-repudiation. It will not claim that CF, SCITT, or Agent Action Capsule already integrate.

## Structure and evidence

Create `research/scitt-agent-action-capsule.md` with the required four sections and frontmatter.
Use the IETF SCITT organization and working-group pages, SCITT architecture/receipts material,
and the Agent Action Capsule repository, README, specification, registry, and Datatracker
draft. Explicitly state that Agent Action Capsule is an individual Internet-Draft, not an
adopted WG document or RFC.

## Validation

Run Devbox validation and tests, inspect whitespace/staged files, commit the note and plan on
`research/scitt-agent-action-capsule`, push, and open a PR targeting `main` without unrelated
artifacts.
