# Design

The web app lives in `web/`. This file covers how it looks and how its copy reads.

## Look

- Base: a dark Certivity-ink canvas with a strict grid, flush left. The printed report (`lib/report`) stays white paper with black type, shown on the ink canvas in the app.
- Palette: Certivity's tokens in `web/frontend/src/routes/layout.css` (`cv-ink-*`, `cv-teal-*`, `cv-mint-*`) plus the app tokens built on them: `canvas`, `panel`, `select` for surfaces, `fg`, `muted`, `faint` for text, `line`, `line-strong` for rules. Use the tokens, never raw `black` or `white`, in app components.
- Accent: `cv-teal-400` for the one primary action per view and for numerals, `cv-mint-300` for selection markers and hover. Neither is a large fill.
- Type has three voices: Instrument Serif (`font-display`, `.ui-display`) for page titles and large numerals, with one italic word for emphasis; Hanken Grotesk for body text at 13px; JetBrains Mono (`font-mono`, `.ui-label`) in small uppercase for labels, metadata, ids and file names.
- Branding: "sudo" in Hanken Grotesk bold in the app bar, "In collaboration with Certivity" beside it as a mono label. Logo directions are in `web/frontend/static/brand/`.
- Structure comes from 1px low-contrast rules, whitespace and the grid. Panels (`.ui-panel`) are one step lighter than the canvas with a 1px `line` border; use them for working areas like the spec editor, not as decorative cards.
- Corners are 3px on buttons, inputs and panels. Buttons are 1px outlines; only the primary one is filled.
- No gradients, glows, blur, glassmorphism or drop shadows.

## Avoid AI-isms

These read as generated. Don't use them in UI copy, docs or commit messages.

- The middle dot `·` as a separator. Use a line break, a comma, a slash, or put the parts in separate elements.
- The em dash `—` as a general-purpose joiner. Rewrite with a comma, colon or full stop.
- Emoji, sparkle icons, and "AI" badges.
- Pill-shaped chips and large rounded corners (`rounded-xl`, `rounded-full`) on cards and buttons.
- Purple or blue gradients, gradient text.
- Filler words: "seamless", "effortless", "powerful", "unlock", "leverage", "elevate", "delve", "robust", "cutting-edge".
- Title Case Headings. Use sentence case.
- Three-item rhetorical lists and taglines ("Fast. Accurate. Compliant.").
- Exclamation marks in system copy.
- Decorative arrows (`→`) in labels where a plain word works.
