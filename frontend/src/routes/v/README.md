# Style variants

Ten looks for the same v1 layout. Each variant is `src/routes/v/NN/+page.svelte` (plus optional components in `src/routes/v/NN/`). Edit nothing outside your folder. Call `app.demo()` in `onMount` so results are filled in on open. Bits UI only for components; Tailwind v4 for styling; load fonts via `<svelte:head>` (Google Fonts).

## State: `import { app } from '#lib/app.svelte.ts'`

Types are in `#lib/types.ts`.

Fields (reactive): `cases: string[]`, `regulations: Regulation[]`, `selectedCase: string`, `spec: string` (bindable), `image: File | null`, `imageUrl: string | null`, `loading: boolean`, `error: string`, `result: RequirementsResult | null`, `selectedId: string | null`.

Derived: `byRegulation: RegulationGroup[]` (`{regulation, title, count, requirements}`), `selected: Requirement | null`.

Methods: `init()`, `demo()` (init, load `dev-rear-lamp`, submit), `loadCase(name: string)`, `setSpecFile(file)`, `setImageFile(file)`, `submit()`, `download()`, `select(id: string | null)`, `regulationTitle(reg: string): string`, `pdfUrl(source: Source): string | null`.

## Palette (Tailwind classes, e.g. `bg-cv-mint-50`, `text-cv-ink-800`)

`cv-ink-950 #02312F`, `cv-ink-800 #11504B`, `cv-teal-700 #0B7A70`, `cv-teal-500 #0EBEA9`, `cv-teal-400 #27DAC2`, `cv-mint-300 #79F2DE`, `cv-mint-50 #F0FDFA`, plus `white` and `black`.

## Layout contract

Every variant has:

- (a) input: case picker (Bits UI `Select`), spec textarea or upload, image upload, image preview
- (b) Run button with loading state, and error display
- (c) cited-regulations summary: title and requirement count
- (d) requirement list: id, text, regulation, version, page (link to `pdfUrl`, new tab), paragraph
- (e) selecting a requirement shows its source page inline in an `<iframe src={pdfUrl}>` (panel, drawer or dialog)
- (f) Download JSON

## Branding

The product is called **sudo**, built with Certivity. Every variant shows a prominent "sudo" wordmark and a small Certivity credit, such as "in collaboration with Certivity" or a small "Certivity" line above a large "sudo". Style both in the variant's own look.
