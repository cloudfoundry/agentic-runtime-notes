# Rating Recalibration Design

## Purpose

Replace the initial coarse heuristic scores with evidence-based ratings derived from a full review of every research note and idea. The new ratings should be semantically meaningful, comparatively consistent, and useful across the generated matrices without forcing an artificial distribution.

## Evaluation method

Use independent full-note review followed by corpus calibration.

During the independent pass, read each complete Markdown document and score it against the fixed rubrics below without using the existing value as an anchor. Rewrite every rating note to cite evidence specific to that document.

During corpus calibration, compare the complete score table for inconsistent relative judgments, unexpectedly narrow ranges, excessive duplicate values, strong correlations, and matrix quadrant occupancy. Adjust a value only when the comparison reveals an inconsistency with the rubric or with similarly situated notes. Do not assign quotas or stretch scores merely to populate quadrants.

## Rating definitions

### Platform impact

`platform-impact` measures the size and depth of the current Cloud Foundry capability gap exposed by the note.

- `0`: Cloud Foundry already provides the capability directly and adequately.
- `25`: A small gap exists around integration, ergonomics, or packaging.
- `50`: Relevant CF primitives exist, but meaningful integration or capability is missing.
- `75`: A substantial platform capability is absent or fragmented.
- `100`: A foundational capability is effectively absent and would require major platform work.

### Maturity

`maturity` measures the technology's production adoption, stability, standardization, and operational evidence.

- `0`: Speculative concept with no demonstrated implementation.
- `25`: Early implementation or experimental specification.
- `50`: Credible implementation with limited production evidence or stability.
- `75`: Production-capable technology with meaningful adoption and operational evidence.
- `100`: Stable, standardized, broadly proven technology with long-term operational evidence.

### Novelty

`novelty` measures how new or unconventional the underlying technical architecture or capability is in the wider ecosystem.

- `0`: Conventional, long-established architecture or capability.
- `25`: Familiar architecture adapted to an agent context.
- `50`: A newer combination or substantial adaptation of known patterns.
- `75`: An emerging architecture with limited precedent.
- `100`: A genuinely novel architecture or capability with almost no prior art.

### Actionability

`actionability` measures how directly the note supports a concrete Cloud Foundry experiment, investigation, or RFC next step.

- `0`: No concrete CF next step follows from the note.
- `25`: The connection is speculative and needs broad discovery first.
- `50`: Plausible next steps exist but require substantial scoping.
- `75`: A bounded experiment or investigation follows with manageable open questions.
- `100`: The note directly defines a well-bounded experiment, investigation, or RFC question.

## Rating notes

Each rating retains the existing `value` and `note` structure. The note must explain the score using document-specific evidence rather than repeating a generic rubric statement. Where relevant, it should mention demonstrated adoption, specification state, available CF primitives, missing CF capability, or a concrete next step.

## Coverage and safeguards

Re-evaluate every non-template Markdown file under `research/` and `ideas/`, including untracked contributions present in the working tree when the pass begins. Every document must contain all four ratings and non-empty notes.

Add automated checks that report each rating's minimum, maximum, distinct-value count, and quadrant occupancy. These checks should detect severe collapse, such as every value occupying one side of the midpoint, but must use conservative thresholds and must not prescribe a target distribution.

The generated HTML must be regenerated after recalibration. Existing interaction and styling fixes remain separate from the scoring logic.

## Verification

Run note validation, rating coverage tests, distribution safeguards, generator tests, generated-artifact freshness checks, and whitespace checks. Review a corpus summary showing ranges, quartiles, duplicate counts, correlations, and quadrant occupancy before accepting the recalibration.
