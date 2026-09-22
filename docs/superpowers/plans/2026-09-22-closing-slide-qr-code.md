# Closing Slide QR Code Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a scanable QR code for the Agentic Runtime Notes site to the closing call-to-action slide.

**Architecture:** Store a self-contained SVG QR asset beside the other deck assets, then reference it in the closing slide's open right column. Extend the existing deck validator to require the QR's target URL, so the encoded destination cannot silently drift.

**Tech Stack:** Marp Markdown, SVG, Node.js validation script, Chromium rendering checks.

---

### Task 1: Generate and protect the QR asset

**Files:**
- Create: `presentation/assets/agentic-runtime-notes-qr.svg`
- Modify: `presentation/scripts/validate-deck.mjs:6-20`

- [ ] **Step 1: Add a failing target-URL check**

Add the canonical URL to the `required` array in `presentation/scripts/validate-deck.mjs`:

```js
'https://cloudfoundry.github.io/agentic-runtime-notes/',
```

- [ ] **Step 2: Run the validator to verify it fails**

Run: `devbox run -- npm run test`

Expected: `Error: missing required text: https://cloudfoundry.github.io/agentic-runtime-notes/`

- [ ] **Step 3: Create the self-contained SVG**

Generate `presentation/assets/agentic-runtime-notes-qr.svg` for exactly:

```text
https://cloudfoundry.github.io/agentic-runtime-notes/
```

Use a white quiet zone of at least four QR modules and `#1b3b51` modules on a white background. Include the URL in the SVG's accessible `<title>` and `<desc>`.

- [ ] **Step 4: Decode the generated QR code**

Rasterize the SVG and decode it with a local QR decoder. Confirm the decoded result is exactly:

```text
https://cloudfoundry.github.io/agentic-runtime-notes/
```

- [ ] **Step 5: Commit the asset and validation guard**

```bash
git add presentation/assets/agentic-runtime-notes-qr.svg presentation/scripts/validate-deck.mjs
git commit -m "feat: add agentic runtime notes qr asset"
```

### Task 2: Add the QR code to the closing slide

**Files:**
- Modify: `presentation/slides.md:264-283`

- [ ] **Step 1: Add the QR image and caption**

Place the following directly after the existing printed URL in the closing slide:

```markdown
![w:190](assets/agentic-runtime-notes-qr.svg)

<div class="eyebrow">Scan to join the work</div>
```

Use the closing slide's right column for the QR by applying the existing theme's layout hooks or a small slide-local wrapper. Preserve the original URL as the non-camera fallback.

- [ ] **Step 2: Update speaker notes**

Add one sentence after the existing participation ask:

```text
The QR code goes to the notes site, where attendees can follow and contribute after the session.
```

- [ ] **Step 3: Build and run the validator**

Run:

```bash
devbox run -- npm run slides:html
devbox run -- npm run test
```

Expected: HTML generation succeeds and the validator reports 11 slides and 4 images.

- [ ] **Step 4: Verify the built output in Chromium**

Confirm:

```text
- agentic-runtime-notes-qr.svg has non-zero natural dimensions.
- The closing slide's scroll height does not exceed its client height.
- The image source resolves to assets/agentic-runtime-notes-qr.svg.
```

- [ ] **Step 5: Commit the closing-slide integration**

```bash
git add presentation/slides.md
git commit -m "feat: add qr code to closing slide"
```

### Task 3: Publish the completed design and implementation records

**Files:**
- Create: `docs/superpowers/specs/2026-09-22-agentic-runtime-notes-qr-design.md`
- Create: `docs/superpowers/plans/2026-09-22-closing-slide-qr-code.md`

- [ ] **Step 1: Force-add the ignored design records**

```bash
git add -f docs/superpowers/specs/2026-09-22-agentic-runtime-notes-qr-design.md docs/superpowers/plans/2026-09-22-closing-slide-qr-code.md
git commit -m "docs: record closing slide qr design"
```

- [ ] **Step 2: Push the branch**

```bash
git push
```
