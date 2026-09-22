# Closing Slide QR Code Design

## Purpose

Give Summit attendees a direct, scanable route to the Agentic Runtime Notes
site from the closing call-to-action slide.

## Scope

- Add a static SVG QR code for
  `https://cloudfoundry.github.io/agentic-runtime-notes/`.
- Place it in the open right column of the closing slide.
- Keep the existing printed URL as a readable fallback.
- Add a concise scan instruction below the code.

## Design

The QR code is a self-contained SVG with a white quiet zone and dark navy
modules. It is displayed at approximately 190 pixels wide, large enough for
audience scanning while leaving the existing call-to-action copy unchanged.
The caption reads `SCAN TO JOIN THE WORK` in the deck's eyebrow styling.

## Verification

- Decode the generated SVG or a rasterized rendering and confirm its URL
  exactly matches the target.
- Run the deck validator and HTML build.
- Use Chromium to confirm the image loads from the built output and the
  closing slide has no vertical overflow.
