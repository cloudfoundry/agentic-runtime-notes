# Workshop Focus Use Cases Design

## Purpose

Extend the generated research map to present the working group's workshop outcomes. The page will lead with two selected focus use cases, connect them to three candidate platform primitives, and let participants inspect the research and ideas supporting either layer or their intersection.

Use cases describe desired workload outcomes. Platform primitives describe reusable Cloud Foundry capabilities that may support those outcomes. They remain separate curated layers over the same evidence corpus.

## Workshop framing

Replace language that presents the page as workshop input. The heading and introduction state that the page summarizes workshop results: two focus use cases, three candidate platform primitives, and the collected evidence behind them.

The visual hierarchy is:

1. Workshop outcome heading and summary.
2. Two focus use-case cards.
3. Three candidate platform-primitive cards.
4. Six tabbed rating matrices.

## Focus use cases

### CF-hosted coding harnesses

App developers run coding harnesses and agents, such as OpenCode, inside Cloud Foundry. A session owns a mutable repository workspace and performs edit/test feedback loops. The untrusted harness submits a candidate artifact to a narrow trusted deployment broker. The broker validates target, policy, provenance, and approval before creating conventional CF packages, builds, deployments, and revisions.

The harness never receives unrestricted CAPI, Git, model, or package-registry credentials. Relevant concerns include persistent workspaces, reusable toolchains, stronger isolation, mediated egress, deployment approvals, stale-base detection, provenance, rollback, and audit.

### User-facing agentic applications

Developers deploy CF applications that use agent frameworks to perform agentic tasks for their users. The routed application authenticates users, creates durable sessions/executions, invokes authorized tools, pauses for approvals, and may use isolated workers for generated code.

Relevant concerns include durable execution identity, user delegation, tool authorization, memory/state services, framework-neutral suspension, multi-tenant quotas, scaling, SLOs, telemetry, and optional sandbox lifecycle.

## Content model

Add `scripts/focus_use_cases.yaml`. Each use case contains:

- Stable unique ID and title.
- Workshop outcome statement.
- Primary actor and beneficiary.
- End-to-end lifecycle.
- Authority boundary.
- Unique capabilities.
- Failure domain.
- Candidate POC.
- RFC decisions unlocked.
- Ordered core and supporting note paths.
- Applicability for each platform primitive: `core`, `conditional`, or `supporting`.

The initial IDs are `cf-hosted-coding-harnesses` and `user-facing-agentic-applications`.

The generator validates exactly two use cases, required non-empty fields, unique IDs, non-empty core memberships, no duplicate note memberships within a use case, known note paths, known primitive IDs, and applicability values from the allowed set.

Membership is curated rather than inferred from tags. A note may belong to both use cases.

## Layout

Render the two use-case cards above the three platform-primitive cards. A use-case card shows its title, workshop outcome, and candidate POC. Expandable content shows actors, lifecycle, authority boundary, failure domain, unique capabilities, RFC decisions, primitive applicability, and linked core/supporting notes.

The existing primitive cards and tabbed matrices remain below. Mobile layouts stack cards and retain the horizontally scrollable matrix tab strip and tall active matrix canvas.

## Selection model

Maintain two independent states: `selectedUseCase` and `selectedPrimitive`.

- With only a use case selected, a note matches when it belongs to that use case.
- With only a primitive selected, a note matches when it belongs to that primitive.
- With both selected, a note matches only when it belongs to both.
- With neither selected, all notes use their normal display.

Each layer has its own **Show all** control. Clicking an already selected card clears only that layer. Cards expose state through `aria-pressed`.

When a selected intersection contains no directly linked notes, display a clear status message instead of silently dimming every marker.

## Matrix and cluster behavior

Matching individual markers retain full saturation and use selection accents. Non-matching markers dim but remain interactive and keyboard reachable.

Cluster markers display `matching/total` while either layer is selected. Cluster pickers sort matching notes first while preserving source order within matching and non-matching groups. All notes remain accessible. Clearing both layers restores total-only cluster counts and original ordering.

Note and cluster-picker dialogs display use-case and primitive membership badges relevant to the current selection.

Matrix tab state and keyboard behavior remain unchanged when selections change.

## Safety and accessibility

All dynamic note and configuration content remains escaped before insertion into dialog markup. Use-case cards, primitive cards, Show-all controls, tabs, markers, and picker items remain keyboard operable. Dialogs retain stable accessible names. Dimmed markers regain full visibility on focus.

## Verification

Tests cover focus-use-case configuration validation, exactly-two enforcement, note/primitive references, applicability values, workshop-result wording, card ordering, card content, independent selection/toggle behavior, intersection matching, empty-intersection status, mixed-cluster matching counts, related-first picker ordering, dialog badges, `aria-pressed`, matrix-tab regression behavior, XSS escaping, responsive structural classes, and all existing interactions.

Regenerate `generated/research-map.html`. Existing note validation, rating safeguards, primitive validation, generated-artifact freshness, and whitespace checks must continue to pass.
