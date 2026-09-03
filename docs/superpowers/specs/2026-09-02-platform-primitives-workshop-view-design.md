# Platform Primitives Workshop View Design

## Purpose

Turn the generated rating map into a presentable strategic workshop view. The page will explain three candidate Cloud Foundry platform primitives and let participants highlight their supporting research and ideas across six rating matrices.

The primitives are a curated strategic layer over the source notes. They do not alter note ratings, tags, matrix positions, or cluster membership.

## Platform primitives

The initial view presents three primitives:

1. **Durable, Addressable Execution**: stable execution identity, externalized checkpoints, suspend/resume, events, timers, retries, and replaceable compute slices.
2. **Attested Workload Authority and Mediated Tool Access**: exchange platform identity for scoped authority, keep credentials outside workloads, enforce outbound access, and produce attributable audit events.
3. **Session-Scoped Isolated Execution**: reusable staged environments, mutable session workspaces, selectable isolation, controlled networking, and resumable lifecycle.

Each primitive includes a concise proposition, current CF gap, strategic decision unlocked, candidate POC, candidate RFC scope, and ordered core/supporting note memberships.

## Content model

Add `scripts/platform_primitives.yaml` as the curated source. Each entry has a stable unique ID, title, proposition, CF gap, strategic decision, POC description, RFC scope, core note paths, and supporting note paths.

A note may belong to more than one primitive. The generator validates required fields, unique primitive IDs, non-empty core membership, duplicate memberships within one primitive, and that every referenced note path exists in the generated corpus. Invalid configuration fails generation with a clear error.

Strategic membership remains separate from Markdown frontmatter because it is workshop curation rather than descriptive source metadata.

## Layout

Three primitive cards appear above the matrices. Each card shows the title, proposition, and strategic decision. Expandable details expose the CF gap, candidate POC, RFC scope, and linked core/supporting notes.

The six matrices move into an accessible tab set. Only the active matrix is visible. The tab strip is horizontally scrollable on narrow screens; primitive cards stack above it. The active matrix keeps the existing tall mobile canvas.

The page remains a self-contained generated HTML file with no server-side runtime. Existing canonical GitHub note links remain unchanged.

## Highlight interaction

Clicking a primitive card persistently selects it across matrix tabs. Related markers remain fully saturated and receive the primitive accent color. Unrelated markers dim but remain visible, keyboard reachable, and interactive.

Clicking the selected card again or selecting **Show all** clears the filter. Primitive cards expose state through `aria-pressed`.

Individual related-note dialogs show the selected primitive membership. Cluster behavior remains coordinate-based and independent per matrix. When a cluster contains both related and unrelated notes, its marker displays `related/total`, such as `2/5`. The cluster picker lists related notes first, identifies their relationship, and retains access to unrelated notes.

## Tab interaction

Matrix controls use tab semantics: a `tablist`, one `tab` per matrix, and matching `tabpanel` elements. Clicking a tab activates its matrix. Arrow keys move between tabs, Home/End select the first/last tab, and focus follows selection.

The selected primitive remains active while switching tabs. Marker highlighting and mixed-cluster counts are recalculated for the newly active matrix.

## Visual language

Each primitive receives a distinct accent color used for its selected card, highlighted markers, related-note badges, and mixed-cluster counts. The colors must remain legible against the existing dark map palette. Cards, tabs, dialogs, and note lists inherit the page typography and controls avoid browser-default grey styling.

## Verification

Tests cover primitive configuration validation, required fields, unknown note paths, duplicate membership, card content, tab and panel markup, keyboard tab behavior, persistent primitive selection, clear behavior, dimming, mixed-cluster related counts, related-first picker ordering, `aria-pressed`, tab semantics, and responsive structural classes.

Regenerate `generated/research-map.html`. Existing note validation, distribution safeguards, generator tests, generated-artifact freshness checks, and whitespace checks must continue to pass.
