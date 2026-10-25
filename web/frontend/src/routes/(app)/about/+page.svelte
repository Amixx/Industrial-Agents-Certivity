<script lang="ts">
// [name, description, diagram subtitle, served by the Anthropic API]
const stages: [string, string, string, boolean][] = [
	[
		'Product profile',
		'Opus reads the spec and the exploded view and lists the parts, functions, vehicle category and electronics.',
		'Reads spec and exploded view',
		true,
	],
	[
		'Regulation pick',
		'The obligation base ranks the 36 UN regulations by scope; Opus picks the applicable ones, each with a probability.',
		'Ranks 36, picks with probability',
		true,
	],
	[
		'Paragraph screening',
		'The Jev decision model answers calibrated yes/no questions about every paragraph of the chosen regulations and combines them into the probability that an expert cites it.',
		'Jev scores every paragraph',
		false,
	],
	[
		'Relevance ranking',
		'Opus scores how relevant each paragraph is to the product; blended with the Jev score, it ranks the paragraphs and the top share goes on.',
		'Blended with Jev, top kept',
		true,
	],
	[
		'Obligation drafts',
		'Opus rewrites each selected paragraph into standalone EARS obligations that keep the numbers and quote the source.',
		'EARS obligations with quotes',
		true,
	],
	[
		'Expert-likeness cut',
		'Opus scores each draft for whether an expert would list it and how central its section is; rules drop pointers and approval marks.',
		'Keep score times section score',
		true,
	],
	[
		'Consolidation',
		'Opus decides which lists an expert writes as one requirement or several; rules drop duplicates and cap the length.',
		'Merge or split lists',
		true,
	],
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

<div class="min-h-0 flex-1 overflow-auto pb-16 text-[15px]">
	<div class="ui-grid">
		<div class="col-span-12 lg:col-span-7">
			<span class="ui-label text-[12px]">About</span>
			<h1 class="ui-display mt-3 text-[3.25rem]">Requirements from a spec, <i>cited</i></h1>
			<p class="mt-5 max-w-[60ch] text-[18px] leading-relaxed text-muted">
				sudo reads a product specification and its exploded view, decides which UN regulations
				apply, and writes the requirement list a homologation engineer would start from. Every
				requirement quotes the regulation and points to its page, so a reviewer checks it in seconds
				instead of searching for it.
			</p>
		</div>
	</div>

	<section class="ui-grid ui-section mt-12">
		<div class="col-span-12 lg:col-span-3">
			<span class="ui-label text-[12px]">Architecture</span>
			<h2 class="ui-display mt-3 text-[2.25rem]">The engine</h2>
		</div>
		<div class="col-span-12 lg:col-span-9">
			<svg
				viewBox="0 0 680 650"
				class="w-full max-w-[760px]"
				role="img"
				aria-labelledby="arch-title"
			>
				<title id="arch-title">
					Seven stages turn the product spec into a requirement list. Opus serves every stage except
					the screening, which the Jev decision model runs; the obligation base feeds the regulation
					pick, and deterministic rules run in the cut and the consolidation.
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
							stroke="context-stroke"
							stroke-width="1.5"
							stroke-linecap="round"
							stroke-linejoin="round"
						/>
					</marker>
				</defs>
				<g class="node-ext">
					<rect x="270" y="20" width="170" height="40" rx="3" />
					<text x="355" y="45" class="t">Product spec</text>
				</g>
				<line x1="355" y1="62" x2="355" y2="84" class="a" marker-end="url(#arr)" />
				{#each stages as [name, , sub, api], i}
					{@const sy = 86 + i * 70}
					<g class="node">
						<rect x="230" y={sy} width="250" height="52" rx="3" />
						<text x="355" y={sy + 22} class="t">{name}</text>
						<text x="355" y={sy + 40} class="s">{sub}</text>
					</g>
					{#if i < stages.length - 1}
						<line x1="355" y1={sy + 54} x2="355" y2={sy + 68} class="a" marker-end="url(#arr)" />
					{/if}
					{#if api}
						<line x1="518" y1={sy + 26} x2="484" y2={sy + 26} class="api" marker-end="url(#arr)" />
					{/if}
				{/each}
				<line x1="355" y1="560" x2="355" y2="588" class="a" marker-end="url(#arr)" />
				<g class="node-ext">
					<rect x="260" y="590" width="190" height="40" rx="3" />
					<text x="355" y="615" class="t">Requirement list</text>
				</g>
				<g class="node-api">
					<rect x="520" y="86" width="140" height="472" rx="3" />
					<text x="590" y="314" class="t">Anthropic API</text>
					<text x="590" y="334" class="s">Opus 5.5</text>
				</g>
				<g class="node-ext">
					<rect x="12" y="156" width="204" height="52" rx="3" />
					<text x="114" y="178" class="t">Obligation base</text>
					<text x="114" y="196" class="s">SQLite scope cards</text>
				</g>
				<g class="node-jev">
					<rect x="12" y="226" width="204" height="52" rx="3" />
					<text x="114" y="248" class="t">Decision model (Jev)</text>
					<text x="114" y="266" class="s">TypeSafe, calibrated yes/no</text>
				</g>
				<g class="node-ext">
					<rect x="12" y="436" width="204" height="122" rx="3" />
					<text x="114" y="462" class="t">Rules</text>
					{#each [
						'Boilerplate filter',
						'Verbatim quotes',
						'Duplicate drop',
						'2,000-character cap',
					] as r, j}
						<text x="114" y={484 + j * 19} class="s">{r}</text>
					{/each}
				</g>
				{#each [182, 252, 462, 532] as ly}
					<line x1="218" y1={ly} x2="226" y2={ly} class="a" marker-end="url(#arr)" />
				{/each}
			</svg>
			<p class="mt-3 max-w-[760px] text-[13px] text-faint">
				Opus 5.5 in our best runs. The hosted app runs Sonnet 5.5 and Haiku 5.5.
			</p>
			<ol class="mt-8 grid max-w-[760px] gap-x-8 gap-y-5 sm:grid-cols-2">
				{#each stages as [name, desc], i}
					<li class="border-t border-line pt-3">
						<span class="ui-label text-[12px]">{String(i + 1).padStart(2, '0')}</span>
						<div class="mt-1 text-[17px] font-semibold">{name}</div>
						<p class="mt-1 leading-relaxed text-muted">{desc}</p>
					</li>
				{/each}
			</ol>
		</div>
	</section>

	<section class="ui-grid ui-section mt-12">
		<div class="col-span-12 lg:col-span-3">
			<span class="ui-label text-[12px]">Experiments</span>
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
					<dt class="ui-label text-[12px]">Uploads on the worked example</dt>
					<dd class="ui-numeral mt-2 text-6xl">60+</dd>
				</div>
				<div class="border-t border-line pt-3">
					<dt class="ui-label text-[12px]">Model families compared</dt>
					<dd class="ui-numeral mt-2 text-6xl">5</dd>
				</div>
				<div class="border-t border-line pt-3">
					<dt class="ui-label text-[12px]">Best worked example F2</dt>
					<dd class="ui-numeral mt-2 text-6xl">79.4</dd>
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
svg .node-jev rect {
	fill: none;
	stroke: var(--color-fg);
	stroke-width: 1;
}
svg .node-api rect {
	fill: none;
	stroke: var(--color-accent);
	stroke-width: 1;
	stroke-dasharray: 4 3;
}
svg .t {
	fill: var(--color-fg);
	font-size: 15px;
	font-weight: 600;
	text-anchor: middle;
}
svg .s {
	fill: var(--color-muted);
	font-size: 12.5px;
	text-anchor: middle;
}
svg .a {
	stroke: var(--color-muted);
	stroke-width: 1;
}
svg .api {
	stroke: var(--color-accent);
	stroke-width: 1;
}
svg .grid {
	stroke: var(--color-line);
	stroke-width: 1;
}
svg .tick {
	fill: var(--color-faint);
	font-family: var(--font-mono);
	font-size: 12px;
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
	font-size: 13.5px;
}
</style>
