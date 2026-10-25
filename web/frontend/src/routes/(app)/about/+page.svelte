<script lang="ts">
import { cubicOut } from 'svelte/easing';
import { Tween } from 'svelte/motion';

// Who does the work in each stage, one column each in the table.
const parts = ['Language model', 'Jev', 'Obligation base', 'Rules'] as const;
type Part = (typeof parts)[number];

const stages: { name: string; desc: string; by: Part[] }[] = [
	{
		name: 'Product profile',
		desc: 'Reads the spec and the exploded view and lists the parts, functions, vehicle category and electronics.',
		by: ['Language model'],
	},
	{
		name: 'Regulation pick',
		desc: 'The obligation base ranks the 36 UN regulations by scope. The model keeps the ones that apply, each with a probability.',
		by: ['Language model', 'Obligation base'],
	},
	{
		name: 'Paragraph screening',
		desc: 'Jev asks calibrated yes/no questions about every paragraph of those regulations and turns the answers into the probability that an expert cites it.',
		by: ['Jev'],
	},
	{
		name: 'Relevance ranking',
		desc: 'The model scores how relevant each paragraph is to this product. Blended with the Jev score, that ranks the paragraphs, and the top share goes on.',
		by: ['Language model', 'Jev'],
	},
	{
		name: 'Obligation drafts',
		desc: 'Each selected paragraph becomes standalone EARS obligations that keep the numbers and quote the source.',
		by: ['Language model'],
	},
	{
		name: 'Expert-likeness cut',
		desc: 'The model scores whether an expert would list each draft and how central its section is. Rules drop boilerplate and check that quotes are verbatim.',
		by: ['Language model', 'Rules'],
	},
	{
		name: 'Consolidation',
		desc: 'The model decides which lists an expert writes as one requirement and which as several. Rules drop duplicates and cap each requirement at 2,000 characters.',
		by: ['Language model', 'Rules'],
	},
];

// Tracing one part: hover previews it, click keeps it.
let pinned = $state<Part | null>(null);
let hovered = $state<Part | null>(null);
const traced = $derived(hovered ?? pinned);
const uses = (i: number, p: Part) => stages[i]?.by.includes(p) ?? false;
const pin = (p: Part) => (pinned = pinned === p ? null : p);

const still = matchMedia('(prefers-reduced-motion: reduce)').matches;

// Adds `in` once the element scrolls into view; the CSS below plays its entrance from there.
function reveal(node: HTMLElement, onIn?: () => void) {
	const io = new IntersectionObserver(
		([e]) => {
			if (!e.isIntersecting) return;
			node.classList.add('in');
			onIn?.();
			io.disconnect();
		},
		{ threshold: 0.15 },
	);
	io.observe(node);
	return { destroy: () => io.disconnect() };
}

const stats = [
	{ label: 'Uploads on the worked example', value: 60, digits: 0, suffix: '+' },
	{ label: 'Model families compared', value: 5, digits: 0, suffix: '' },
	{ label: 'Best worked example F2', value: 79.4, digits: 1, suffix: '' },
];
const counts = stats.map(() => new Tween(0, { duration: still ? 0 : 1400, easing: cubicOut }));
const countUp = () => stats.forEach((st, i) => counts[i].set(st.value));

// Worked example (rear lamp), requirement F2 on the platform, cost of one run in US dollars.
const runs = [
	{ label: 'Rules only', cost: 0, f2: 0.348, dx: 8, dy: 4 },
	{ label: 'Local model, drafting', cost: 0, f2: 0.551, dx: 10, dy: 14 },
	{ label: 'Sonnet', cost: 3.08, f2: 0.634, dx: 6, dy: 18 },
	{ label: 'Opus', cost: 6.36, f2: 0.651, dx: 6, dy: 18 },
	{ label: 'Fable', cost: 16.52, f2: 0.682, dx: -8, dy: 4 },
	{ label: 'Full engine, API', cost: 9.35, f2: 0.772, dx: 4, dy: 22 },
	{ label: 'Full engine, best', cost: 14.4, f2: 0.794, dx: -8, dy: -10 },
];
const frontier = [
	'Rules only',
	'Local model, drafting',
	'Sonnet',
	'Opus',
	'Full engine, API',
	'Full engine, best',
];

const W = 640,
	H = 300,
	L = 52,
	R = 20,
	T = 16,
	B = 40;
const x = (c: number) => L + (c / 18) * (W - L - R);
const y = (f: number) => T + (1 - (f - 0.3) / 0.55) * (H - T - B);
const front = runs
	.filter((r) => frontier.includes(r.label))
	.sort((a, b) => a.cost - b.cost || a.f2 - b.f2);
const path = front.map((r, i) => `${i ? 'L' : 'M'}${x(r.cost)} ${y(r.f2)}`).join(' ');
</script>

<svelte:head><title>About | sudo</title></svelte:head>

<div class="min-h-0 flex-1 overflow-auto pb-16 text-[16px]">
	<div class="reveal ui-grid" use:reveal>
		<div class="col-span-12 lg:col-span-7">
			<span class="ui-label text-[13px]">About</span>
			<h1 class="ui-display mt-3 text-[3.25rem]">Requirements from a spec, <i>cited</i></h1>
			<p class="mt-5 max-w-[60ch] text-[18px] leading-relaxed text-muted">
				sudo reads a product specification and its exploded view, decides which UN regulations
				apply, and writes the requirement list a homologation engineer would start from. Every
				requirement quotes the regulation and points to its page, so a reviewer checks it in seconds
				instead of searching for it.
			</p>
		</div>
	</div>

	<section class="reveal ui-grid ui-section mt-12" use:reveal>
		<div class="col-span-12 lg:col-span-3">
			<span class="ui-label text-[13px]">Architecture</span>
			<h2 class="ui-display mt-3 text-[2.25rem]">The engine</h2>
		</div>
		<div class="col-span-12 lg:col-span-9">
			<p class="max-w-[60ch] leading-relaxed text-muted">
				The spec and its exploded view go in, the requirement list comes out. In between, seven
				stages run in order. A mark shows which part does the work in each one; pick a part to
				trace it.
			</p>
			<div class="mt-6 flex flex-wrap items-center gap-2" role="group" aria-label="Trace a part">
				{#each parts as p}
					<button
						type="button"
						class="ui-toggle border border-line-strong {pinned === p ? 'ui-toggle-on border-mark' : ''}"
						aria-pressed={pinned === p}
						onclick={() => pin(p)}
						onmouseenter={() => (hovered = p)}
						onmouseleave={() => (hovered = null)}
					>
						{p}
						<span class="ml-1 font-mono text-faint">{stages.filter((s) => s.by.includes(p)).length}</span>
					</button>
				{/each}
				{#if pinned}
					<button type="button" class="ui-link ml-1 cursor-pointer text-xs" onclick={() => (pinned = null)}>
						Show all
					</button>
				{/if}
			</div>
			<table class="mt-4 w-full max-w-[880px] border-collapse text-left">
				<thead>
					<tr class="border-b border-line-strong">
						<th class="w-12 pb-3 align-bottom"><span class="ui-label">#</span></th>
						<th class="pb-3 align-bottom"><span class="ui-label">Stage</span></th>
						{#each parts as p}
							<th class="hidden w-24 px-1 pb-3 text-center align-bottom sm:table-cell">
								<button
									type="button"
									class="ui-label cursor-pointer leading-snug transition-colors hover:text-fg {traced === p
										? 'text-fg'
										: ''}"
									aria-pressed={pinned === p}
									onclick={() => pin(p)}
									onmouseenter={() => (hovered = p)}
									onmouseleave={() => (hovered = null)}
								>
									{p}
								</button>
							</th>
						{/each}
					</tr>
				</thead>
				<tbody>
					{#each stages as s, i}
						{@const off = traced !== null && !s.by.includes(traced)}
						<tr class="stage border-b border-line align-top" style="--d: {200 + i * 90}ms">
							<td class="pt-6 transition-opacity duration-200 {off ? 'opacity-30' : ''}">
								<span class="ui-label">{String(i + 1).padStart(2, '0')}</span>
							</td>
							<td class="py-5 pr-8 transition-opacity duration-200 {off ? 'opacity-30' : ''}">
								<div class="text-[17px] font-semibold">{s.name}</div>
								<p class="mt-1 max-w-[56ch] leading-relaxed text-muted">{s.desc}</p>
								<p class="ui-label mt-2 sm:hidden">{s.by.join(', ')}</p>
							</td>
							{#each parts as p}
								{@const on = s.by.includes(p)}
								{@const dim = traced !== null && traced !== p}
								<td
									class="lane relative hidden transition-opacity duration-200 sm:table-cell {traced === p
										? 'lane-on'
										: ''} {dim ? 'opacity-30' : ''}"
								>
									{#if on && uses(i - 1, p)}<span class="run run-up"></span>{/if}
									{#if on && uses(i + 1, p)}<span class="run run-down"></span>{/if}
									{#if on}
										<span class="mark relative mx-auto mt-[1.6rem] block size-3 bg-mark" aria-label={p}></span>
									{/if}
								</td>
							{/each}
						</tr>
					{/each}
				</tbody>
			</table>
			<dl class="mt-8 grid max-w-[880px] gap-x-8 gap-y-4 text-[14px] leading-snug text-muted sm:grid-cols-2 lg:grid-cols-4">
				<div>
					<dt class="ui-label">Language model</dt>
					<dd class="mt-1">Opus 5.5 in our best runs. The hosted app uses Sonnet 5.5 and Haiku 5.5.</dd>
				</div>
				<div>
					<dt class="ui-label">Jev</dt>
					<dd class="mt-1">A TypeSafe decision model with calibrated yes/no answers.</dd>
				</div>
				<div>
					<dt class="ui-label">Obligation base</dt>
					<dd class="mt-1">Scope cards for the 36 regulations, in SQLite.</dd>
				</div>
				<div>
					<dt class="ui-label">Rules</dt>
					<dd class="mt-1">Fixed checks: boilerplate, verbatim quotes, duplicates, length.</dd>
				</div>
			</dl>
		</div>
	</section>

	<section class="reveal ui-grid ui-section mt-12" use:reveal>
		<div class="col-span-12 lg:col-span-3">
			<span class="ui-label text-[13px]">Experiments</span>
			<h2 class="ui-display mt-3 text-[2.25rem]">Cost against <i>quality</i></h2>
			<p class="mt-4 leading-relaxed text-muted">
				Score on the worked example (rear lamp) against the cost of one run. The line is the
				frontier: no other setup we tried scores higher for less. Sonnet, Opus and Fable are one
				model pass without the engine.
			</p>
		</div>
		<div class="col-span-12 lg:col-span-9">
			<svg
				viewBox="0 0 {W} {H}"
				class="w-full max-w-[760px]"
				role="img"
				aria-labelledby="pareto-title"
			>
				<title id="pareto-title">
					Requirement F2 against cost per run for seven setups on the worked example.
				</title>
				{#each [0.3, 0.4, 0.5, 0.6, 0.7, 0.8] as g}
					<line x1={L} x2={W - R} y1={y(g)} y2={y(g)} class="grid" />
					<text x={L - 8} y={y(g) + 4} class="tick" text-anchor="end">{g.toFixed(1)}</text>
				{/each}
				{#each [0, 5, 10, 15] as c}
					<text x={x(c)} y={H - B + 18} class="tick" text-anchor="middle">${c}</text>
				{/each}
				<text x={W - R} y={H - 4} class="tick" text-anchor="end">Cost per run, USD</text>
				<path d={path} class="front" pathLength="1" />
				{#each runs as r}
					{@const on = frontier.includes(r.label)}
					{@const k = on ? front.indexOf(r) : front.length + 1}
					<circle
						cx={x(r.cost)}
						cy={y(r.f2)}
						r="4"
						class="dot {on ? 'pt-on' : 'pt-off'}"
						style="--d: {300 + k * 220}ms"
					/>
					<text
						x={x(r.cost) + r.dx}
						y={y(r.f2) + r.dy}
						class="dot pl"
						style="--d: {400 + k * 220}ms"
						text-anchor={r.dx < 0 ? 'end' : 'start'}
					>
						{r.label} {Math.round(r.f2 * 100)}
					</text>
				{/each}
			</svg>
			<dl class="mt-8 grid max-w-[760px] gap-x-8 gap-y-5 sm:grid-cols-3" use:reveal={countUp}>
				{#each stats as st, i}
					<div class="flex flex-col-reverse justify-end border-t border-line pt-4">
						<dt class="ui-label mt-3 text-[13px]">{st.label}</dt>
						<dd class="ui-numeral text-6xl">{counts[i].current.toFixed(st.digits)}{st.suffix}</dd>
					</div>
				{/each}
			</dl>
			<p class="mt-6 max-w-[60ch] leading-relaxed text-muted">
				A bigger model alone moves the score a few points. Most of the gain came from the engine
				around it: choosing paragraphs well, then deciding which drafts an expert would actually
				keep. A 9B model running on a laptop wrote the drafts for 55, with the paragraphs picked by
				a larger model; drafting needs no cloud model.
			</p>
		</div>
	</section>
</div>

<style>
/* A thin guide down each lane, so the marks read as a flow without boxes. */
.lane::before {
	content: '';
	position: absolute;
	top: 0;
	bottom: 0;
	left: 50%;
	width: 1px;
	background: var(--color-line);
	transition: background-color 200ms;
}
.lane-on::before {
	background: var(--color-mark);
}
/* Joins marks in consecutive stages of the same part, like a line on a metro map. */
.run {
	transform-origin: top;
	transition: transform 300ms ease-in-out calc(var(--d, 0ms) + 300ms);
	position: absolute;
	left: calc(50% - 1px);
	width: 3px;
	background: var(--color-mark);
}
.run-up {
	top: 0;
	height: calc(1.6rem + 6px);
}
.run-down {
	top: calc(1.6rem + 6px);
	bottom: 0;
}
.mark {
	transition:
		transform 150ms,
		background-color 150ms;
}
.stage {
	transition:
		background-color 150ms,
		opacity 600ms ease var(--d, 0ms),
		transform 600ms cubic-bezier(0.2, 0.7, 0.2, 1) var(--d, 0ms);
}
.stage:hover {
	background: var(--color-select);
}
.stage:hover .mark {
	background: var(--color-accent);
	transform: scale(1.25);
}

/* Scenes: each block plays its entrance once it scrolls into view. */
.reveal > * {
	transition:
		opacity 700ms ease,
		transform 700ms cubic-bezier(0.2, 0.7, 0.2, 1);
}
.reveal > :nth-child(2) {
	transition-delay: 120ms;
}
.reveal:not(:global(.in)) > * {
	opacity: 0;
	transform: translateY(1.25rem);
}
.reveal:not(:global(.in)) .stage {
	opacity: 0;
	transform: translateY(0.75rem);
}
.reveal:not(:global(.in)) .run {
	transform: scaleY(0);
}
svg .front {
	stroke-dasharray: 1;
	stroke-dashoffset: 0;
	transition: stroke-dashoffset 1600ms cubic-bezier(0.4, 0, 0.2, 1) 250ms;
}
.reveal:not(:global(.in)) svg .front {
	stroke-dashoffset: 1;
}
svg .dot {
	transform-box: fill-box;
	transform-origin: center;
	transition:
		opacity 400ms ease var(--d, 0ms),
		transform 400ms cubic-bezier(0.3, 1.4, 0.5, 1) var(--d, 0ms);
}
.reveal:not(:global(.in)) svg .dot {
	opacity: 0;
	transform: scale(0.4);
}

@media (prefers-reduced-motion: reduce) {
	.mark,
	.stage,
	.lane::before,
	.run,
	.reveal > *,
	svg .front,
	svg .dot {
		transition: none !important;
	}
	.reveal:not(:global(.in)) > *,
	.reveal:not(:global(.in)) .stage,
	.reveal:not(:global(.in)) .run,
	.reveal:not(:global(.in)) svg .dot {
		opacity: 1;
		transform: none;
	}
	.reveal:not(:global(.in)) svg .front {
		stroke-dashoffset: 0;
	}
}
svg .grid {
	stroke: var(--color-line);
	stroke-width: 1;
}
svg .tick {
	fill: var(--color-faint);
	font-family: var(--font-mono);
	font-size: 13px;
}
svg .front {
	fill: none;
	stroke: var(--color-accent);
	stroke-width: 1.5;
}
svg .pt-on {
	fill: var(--color-accent);
}
svg .pt-off {
	fill: none;
	stroke: var(--color-faint);
	stroke-width: 1.5;
}
svg .pl {
	fill: var(--color-fg);
	font-size: 14.5px;
}
</style>
