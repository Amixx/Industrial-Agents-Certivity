# Design

The web app lives in `web/`. This file covers how it looks and how its copy reads.

## Look

- Base: variant 05, Swiss grid (`web/frontend/src/routes/v/05`). Strict grid, flush left, large light numerals, Hanken Grotesk.
- Palette: Certivity's tokens in `web/frontend/src/routes/layout.css` (`cv-ink-*`, `cv-teal-*`, `cv-mint-*`). Mint is an accent for selection and highlights, never a large fill.
- Branding: "sudo" large, "in collaboration with Certivity" small. Logo directions are in `web/frontend/static/brand/`.
- Structure comes from rules, whitespace and the grid, not from boxes, cards or shadows.
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
