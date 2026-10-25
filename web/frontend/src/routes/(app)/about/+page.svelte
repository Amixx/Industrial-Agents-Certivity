<script lang="ts">
const stages = [
	[
		'Product profile',
		'Reads the spec and the exploded view and lists the parts, functions and vehicle category.',
	],
	[
		'Regulation pick',
		'Chooses the applicable UN regulations out of 36, with a probability for each.',
	],
	[
		'Paragraph search',
		'Scores every paragraph of the chosen regulations for relevance, with calibrated yes/no answers from Jev.',
	],
	[
		'Obligation drafts',
		'Turns each relevant paragraph into requirements that quote the regulation and cite its page.',
	],
	[
		'Expert-likeness cut',
		'Scores every draft for whether an expert would list it, and drops the ones that would not.',
	],
	['Consolidation', 'Merges rows an expert writes as one, splits lists, removes duplicates.'],
];

// Worked example (rear lamp), requirement F2 on the platform, cost of one run in US dollars.
const runs = [
	{ label: 'Rules only', cost: 0, f2: 0.348, dx: 8, dy: 4 },
	{ label: 'Local model, drafting', cost: 0, f2: 0.551, dx: 8, dy: 16 },
	{ label: 'Sonnet', cost: 3.08, f2: 0.634, dx: 6, dy: 18 },
	{ label: 'Opus', cost: 6.36, f2: 0.651, dx: 6, dy: 18 },
	{ label: 'Fable', cost: 16.52, f2: 0.682, dx: -8, dy: 4 },
	{ label: 'Full engine, API', cost: 9.35, f2: 0.772, dx: -8, dy: -8 },
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
	L = 48,
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

<div class="min-h-0 flex-1 overflow-auto pb-16">
	<div class="ui-grid">
		<div class="col-span-12 lg:col-span-7">
			<span class="ui-label">About</span>
			<h1 class="ui-display mt-3 text-[2.75rem]">Requirements from a spec, <i>cited</i></h1>
			<p class="mt-5 max-w-[60ch] text-[15px] leading-relaxed text-muted">
				sudo reads a product specification and its exploded view, decides which UN regulations
				apply, and writes the requirement list a homologation engineer would start from. Every
				requirement quotes the regulation and points to its page, so a reviewer checks it in seconds
				instead of searching for it.
			</p>
		</div>
	</div>

	<section class="ui-grid ui-section mt-12">
		<div class="col-span-12 lg:col-span-3">
			<span class="ui-label">Architecture</span>
			<h2 class="ui-display mt-3 text-[1.75rem]">The engine</h2>
		</div>
		<div class="col-span-12 lg:col-span-9">
			<svg
				viewBox="0 0 680 400"
				class="w-full max-w-[760px]"
				role="img"
				aria-labelledby="arch-title"
			>
				<title id="arch-title">
					The product spec goes into the requirement engine, which runs six stages and calls the
					Anthropic API, TypeSafe Jev and the regulation corpus.
				</title>
				<defs>
					<marker
						id="arr"
						viewBox="0 0 10 10"
						refX="8"
						refY="5"
						markerWidth="6"
						markerHeight="6"
						orient="auto-start-reverse"
					>
						<path
							d="M2 1L8 5L2 9"
							fill="none"
							stroke="var(--color-muted)"
							stroke-width="1.5"
							stroke-linecap="round"
							stroke-linejoin="round"
						/>
					</marker>
				</defs>
				<g class="node-ext">
					<rect x="260" y="10" width="160" height="50" rx="3" />
					<text x="340" y="30" class="t">Product spec</text>
					<text x="340" y="47" class="s">Text and drawing</text>
				</g>
				<line x1="340" y1="62" x2="340" y2="86" class="a" marker-end="url(#arr)" />
				<rect x="40" y="88" width="600" height="205" rx="3" class="box" />
				<text x="60" y="110" class="lbl">REQUIREMENT ENGINE</text>
				{#each [
					[70, 125],
					[260, 125],
					[450, 125],
					[450, 220],
					[260, 220],
					[70, 220],
				] as [bx, by], i}
					<g class="node">
						<rect x={bx} y={by} width="160" height="52" rx="3" />
						<text x={bx + 80} y={by + 21} class="t">{stages[i][0]}</text>
						<text x={bx + 80} y={by + 38} class="s">
							{[
								'Parts and functions',
								'From 36 UN regulations',
								'Relevance and Jev',
								'Quoted and cited',
								'Scores every row',
								'Merge, split, dedupe',
							][i]}
						</text>
					</g>
				{/each}
				<line x1="232" y1="151" x2="256" y2="151" class="a" marker-end="url(#arr)" />
				<line x1="422" y1="151" x2="446" y2="151" class="a" marker-end="url(#arr)" />
				<line x1="530" y1="179" x2="530" y2="216" class="a" marker-end="url(#arr)" />
				<line x1="448" y1="246" x2="424" y2="246" class="a" marker-end="url(#arr)" />
				<line x1="258" y1="246" x2="234" y2="246" class="a" marker-end="url(#arr)" />
				{#each [
					[130, 'Anthropic API', 'Opus, Sonnet, Haiku'],
					[340, 'TypeSafe Jev', 'Calibrated yes/no'],
					[550, 'Regulation corpus', 'Obligation base, SQLite'],
				] as [cx, t, s]}
					<line x1={cx} y1="293" x2={cx} y2="330" class="d" />
					<g class="node-ext">
						<rect x={Number(cx) - 90} y="330" width="180" height="52" rx="3" />
						<text x={cx} y="351" class="t">{t}</text>
						<text x={cx} y="368" class="s">{s}</text>
					</g>
				{/each}
			</svg>
			<ol class="mt-8 grid max-w-[760px] gap-x-8 gap-y-5 sm:grid-cols-2">
				{#each stages as [name, desc], i}
					<li class="border-t border-line pt-3">
						<span class="ui-label">{String(i + 1).padStart(2, '0')}</span>
						<div class="mt-1 text-[14px] font-semibold">{name}</div>
						<p class="mt-1 leading-relaxed text-muted">{desc}</p>
					</li>
				{/each}
			</ol>
		</div>
	</section>

	<section class="ui-grid ui-section mt-12">
		<div class="col-span-12 lg:col-span-3">
			<span class="ui-label">Experiments</span>
			<h2 class="ui-display mt-3 text-[1.75rem]">Cost against <i>quality</i></h2>
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
				<path d={path} class="front" />
				{#each runs as r}
					{@const on = frontier.includes(r.label)}
					<circle cx={x(r.cost)} cy={y(r.f2)} r="4" class={on ? 'pt-on' : 'pt-off'} />
					<text
						x={x(r.cost) + r.dx}
						y={y(r.f2) + r.dy}
						class="pl"
						text-anchor={r.dx < 0 ? 'end' : 'start'}
					>
						{r.label} {Math.round(r.f2 * 100)}
					</text>
				{/each}
			</svg>
			<dl class="mt-8 grid max-w-[760px] gap-x-8 gap-y-5 sm:grid-cols-3">
				<div class="border-t border-line pt-3">
					<dt class="ui-label">Uploads on the worked example</dt>
					<dd class="ui-numeral mt-2">60+</dd>
				</div>
				<div class="border-t border-line pt-3">
					<dt class="ui-label">Model families compared</dt>
					<dd class="ui-numeral mt-2">5</dd>
				</div>
				<div class="border-t border-line pt-3">
					<dt class="ui-label">Best worked example F2</dt>
					<dd class="ui-numeral mt-2">79.4</dd>
				</div>
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
svg .box {
	fill: none;
	stroke: var(--color-line-strong);
	stroke-width: 1;
	stroke-dasharray: 4 4;
}
svg .node rect {
	fill: var(--color-panel);
	stroke: var(--color-accent);
	stroke-width: 1;
}
svg .node-ext rect {
	fill: none;
	stroke: var(--color-line-strong);
	stroke-width: 1;
}
svg .t {
	fill: var(--color-fg);
	font-size: 13px;
	font-weight: 600;
	text-anchor: middle;
}
svg .s {
	fill: var(--color-muted);
	font-size: 11px;
	text-anchor: middle;
}
svg .lbl {
	fill: var(--color-muted);
	font-family: var(--font-mono);
	font-size: 10.5px;
	letter-spacing: 0.08em;
}
svg .a {
	stroke: var(--color-muted);
	stroke-width: 1;
}
svg .d {
	stroke: var(--color-faint);
	stroke-width: 1;
	stroke-dasharray: 3 3;
}
svg .grid {
	stroke: var(--color-line);
	stroke-width: 1;
}
svg .tick {
	fill: var(--color-faint);
	font-family: var(--font-mono);
	font-size: 10.5px;
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
	font-size: 11.5px;
}
</style>
