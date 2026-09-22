# SpiceDB Research Note Design

## Goal

Add a sourced research note on SpiceDB as a fine-grained authorization substrate for agents,
tools, and Cloud Foundry resources.

## Scope

The note will cover SpiceDB's Zanzibar-inspired architecture: schema-defined relationships,
permissions, consistency, caveated relationships, reverse lookups, datastore/API boundaries,
and the separation of authentication from authorization. It will then assess a possible CF
integration in which instance identity certificates are verified outside SpiceDB and mapped to
stable authorization subjects.

The CF analysis will use examples involving agents accessing spaces, applications, routes,
service bindings, tools, and other resources. It will discuss a shared SpiceDB service,
relationship synchronization from CAPI/Diego events, certificate rotation and revocation,
tenant isolation, latency/availability, and audit implications. It will not claim that SpiceDB
validates CF instance identity certificates natively.

## Structure

Create `research/spicedb.md` using the repository template and required sections:

1. Summary
2. Key findings
3. CF relevance
4. Open questions

Use provisional ratings and clearly label Cloud Foundry integration ideas as analysis or open
questions rather than existing SpiceDB features.

## Sources and evidence

Use the SpiceDB GitHub repository and README, official concepts/modeling/consistency/API
documentation where available, and the Zanzibar paper link referenced by the project. Claims
about CF instance identity certificates, CAPI/Diego synchronization, and agent authorization
will be framed as proposed integration boundaries.

## Validation

Run the repository's configured Devbox validation and test scripts, inspect whitespace and the
staged diff, then commit the note, plan, and this design spec on `research/spicedb`. Push the
branch and open a new PR targeting `main` without staging unrelated environment artifacts.
