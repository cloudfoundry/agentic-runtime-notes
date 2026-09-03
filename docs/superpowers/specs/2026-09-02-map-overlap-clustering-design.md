# Map Overlap Clustering Design

## Purpose

Make every note reachable when multiple notes occupy the same derived position on a matrix. The behavior is a presentation improvement only: ratings and exact 0-100 positions remain unchanged.

## Clustering behavior

For each configured matrix independently, group placed notes by their exact derived `x/y` pair. Groups with one note render as the existing individual marker. Groups with two or more notes render as one cluster marker at the shared position and display the number of notes.

Near-but-not-identical positions remain separate; no coordinate rounding, jitter, or distance-based grouping is introduced.

Cluster markers have a distinct visual style and an accessible label such as `3 notes at this position`. They are buttons and remain keyboard reachable.

## Cluster picker

Clicking a cluster opens a picker dialog. The picker lists every note in the cluster, including its type, title, and short summary. Each item is an actionable button or link. Selecting an item replaces the picker with the existing single-note detail dialog, which continues to show the full summary, tags, ratings, justifications, and GitHub link.

Both dialogs have one close button and close on Escape. The generated page must not create duplicate close controls when switching between picker and detail views.

## Data flow and implementation

The generator groups each matrix's payload after deriving positions. The generated HTML contains cluster metadata keyed by matrix and position, while the browser-side code handles picker selection and detail rendering. Clustering is recalculated during generation, so changing a rating or plot definition automatically updates the appropriate matrix.

## Verification

Tests cover singleton markers, exact-overlap grouping, separate clustering across matrices, cluster counts and accessible labels, picker note listings, selection into detail view, and the invariant that only one close button exists in the generated dialog markup.
