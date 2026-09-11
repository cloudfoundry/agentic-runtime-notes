# Research Clustering Map Design

## Purpose

Create a static, generated HTML map for the working-group workshop. The map will help participants cluster the repository's research notes and ideas without turning the provisional workshop view into a permanent taxonomy.

## Data model

Both `research/*.md` and `ideas/*.md` notes may contain reusable ratings in YAML frontmatter:

```yaml
ratings:
  platform-impact:
    value: 80
    note: "Touches core runtime and governance concerns across many deployments."
  maturity:
    value: 55
    note: "Strong external prior art, but patterns are still evolving."
```

Each rating has a required integer `value` from 0 through 100 and a required, non-empty `note` justifying the score. Ratings are authored in the note and are not inferred or overwritten by generation.

The initial rating pass will manually score all existing ideas and research notes for:

- `platform-impact`
- `maturity`
- `novelty`
- `actionability`

These are initial working-group judgments and must be labeled provisional in the generated page.

## Plot model

Plot definitions are separate from note ratings and identify axes by rating name. The initial plot is `platform-impact-maturity`:

- x-axis: `maturity`, labeled Maturity, low to high
- y-axis: `platform-impact`, labeled Platform Impact, low to high

The model must support future plots selecting any two existing or future rating names without changing the note schema. A note lacking either selected rating is unplaced for that plot and remains visible in an unplaced list.

## Generator and output

Add a generator under `scripts/` that reads all non-template Markdown notes, parses frontmatter, extracts a short summary, and emits a self-contained static HTML page. Research summaries come from `## Summary`; idea summaries come from `## The idea`; a first substantive paragraph is the fallback.

The generated note data includes type, title, tags, summary, author/date when available, ratings and justifications, source path, and a canonical GitHub URL. The page embeds this data and uses lightweight vanilla HTML, CSS, and JavaScript. It requires no server-side runtime and can be hosted locally or on GitHub Pages.

Provide a repository command to regenerate the page. Validation must fail clearly for malformed frontmatter, invalid rating objects or values, missing rating notes, and duplicate note identifiers.

## Interaction and presentation

Render one marker per placed idea or research note, with distinct visual treatment and a legend. Hover and keyboard focus expose the title and type. Clicking a marker opens an accessible overlay containing the title, type, tags, summary, author/date, ratings with numeric values and justifications, and the direct GitHub Markdown link. Escape closes the overlay.

The page includes axis labels and explains that ratings and positions are provisional. On narrow screens the map becomes a taller, scrollable canvas rather than shrinking labels into unreadability. Unplaced notes are listed separately so new contributions cannot disappear from the workshop view.

## Verification

Tests cover frontmatter extraction, rating validation, coordinate derivation from selected rating values, summary extraction, GitHub URL generation, and representative marker/overlay interactions. The initial rating pass is reviewed for complete coverage and non-empty justifications before the page is considered ready.
