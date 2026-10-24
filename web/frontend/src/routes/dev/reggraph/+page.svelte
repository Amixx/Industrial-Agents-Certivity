<script lang="ts">
import data from './graph.json';

interface GraphNode {
	label: string;
	page: number;
	parent: number;
	gold: boolean;
	text: string;
}

interface RegulationGraph {
	regulation: string;
	version: string;
	nodes: GraphNode[];
	refs: [number, number][];
}

const graphs = data as unknown as RegulationGraph[];
const width = 1200;
const axis = 300;
const tickBase = 6;

let selected = $state('UN R148');
let onlyGolden = $state(false);
let hovered = $state<number | null>(null);

const graph = $derived(graphs.find((g) => g.regulation === selected) ?? graphs[0]);
const step = $derived(width / Math.max(graph.nodes.length - 1, 1));
const depths = $derived.by(() => {
	const memo: number[] = [];
	const depth = (i: number): number => {
		if (memo[i] !== undefined) return memo[i];
		const p = graph.nodes[i].parent;
		memo[i] = p < 0 ? 0 : depth(p) + 1;
		return memo[i];
	};
	return graph.nodes.map((_, i) => depth(i));
});
const labelGap = 24;
const sections = $derived.by(() => {
	const shown: { i: number; label: string }[] = [];
	graph.nodes.forEach((n, i) => {
		const last = shown.at(-1);
		if (
			n.parent < 0 &&
			/^(\d+|Annex \S+)$/.test(n.label) &&
			(!last || (i - last.i) * step >= labelGap)
		) {
			shown.push({ i, label: n.label });
		}
	});
	return shown;
});
const golden = $derived(graph.nodes.flatMap((n, i) => (n.gold ? [i] : [])));
const arcs = $derived(
	graph.refs
		.map(([s, t]) => ({
			s,
			t,
			gold: graph.nodes[s].gold || graph.nodes[t].gold,
			both: graph.nodes[s].gold && graph.nodes[t].gold,
		}))
		.filter((a) => !onlyGolden || a.gold),
);
const stats = $derived({
	golden: golden.length,
	refs: graph.refs.length,
	goldenWithRef: new Set(graph.refs.filter(([s]) => graph.nodes[s].gold).map(([s]) => s)).size,
	goldToGold: graph.refs.filter(([s, t]) => graph.nodes[s].gold && graph.nodes[t].gold).length,
});

function x(i: number): number {
	return i * step;
}

function arcPath(s: number, t: number): string {
	const x1 = x(s);
	const x2 = x(t);
	const r = Math.abs(x2 - x1) / 2;
	const h = Math.min(r, axis - 10);
	return `M ${x1} ${axis} A ${r} ${h} 0 0 ${x2 > x1 ? 1 : 0} ${x2} ${axis}`;
}

function onMove(event: PointerEvent) {
	const svg = event.currentTarget as SVGSVGElement;
	const box = svg.getBoundingClientRect();
	const vx = ((event.clientX - box.left) / box.width) * width;
	hovered = Math.max(0, Math.min(graph.nodes.length - 1, Math.round(vx / step)));
}
</script>

<svelte:head>
	<title>sudo, regulation graph</title>
	<link rel="preconnect" href="https://fonts.googleapis.com">
	<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous">
	<link
		rel="stylesheet"
		href="https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@300;400;500;600;700;800&display=swap"
	>
</svelte:head>

<div class="reggraph-root min-h-screen bg-white px-4 pb-16 text-black md:px-12">
	<header
		class="flex flex-wrap items-end justify-between gap-4 border-t-[6px] border-black pt-3 pb-6"
	>
		<div class="flex items-baseline gap-6">
			<h1 class="text-6xl leading-[0.8] font-bold tracking-[-0.05em]">sudo</h1>
			<p class="text-sm font-medium">Paragraph references inside one regulation</p>
		</div>
		<p class="text-xs">Golden paragraphs from cases/dev-rear-lamp</p>
	</header>

	<nav class="flex flex-wrap items-baseline gap-x-8 gap-y-2 border-t border-black pt-2 text-sm">
		{#each graphs as g (g.regulation)}
			<button
				type="button"
				class="font-medium {g.regulation === selected
					? 'underline decoration-cv-mint-300 decoration-4 underline-offset-4'
					: 'text-cv-ink-800'}"
				onclick={() => {
					selected = g.regulation;
					hovered = null;
				}}
			>
				{g.regulation}
			</button>
		{/each}
		<label class="ml-auto flex items-center gap-2 text-xs">
			<input type="checkbox" bind:checked={onlyGolden}>
			Only references that touch a golden paragraph
		</label>
	</nav>

	<section class="grid grid-cols-2 gap-x-8 gap-y-4 border-t border-black pt-4 mt-8 md:grid-cols-4">
		<div>
			<p class="text-5xl font-light tabular-nums">{graph.nodes.length}</p>
			<p class="text-xs">paragraphs in {graph.regulation}, version {graph.version}</p>
		</div>
		<div>
			<p class="text-5xl font-light tabular-nums">{stats.refs}</p>
			<p class="text-xs">resolved references</p>
		</div>
		<div>
			<p class="text-5xl font-light tabular-nums">{stats.goldenWithRef}/{stats.golden}</p>
			<p class="text-xs">golden paragraphs that cite another paragraph</p>
		</div>
		<div>
			<p class="text-5xl font-light tabular-nums">{stats.goldToGold}</p>
			<p class="text-xs">references from a golden paragraph to another golden one</p>
		</div>
	</section>

	<figure class="mt-10 border-t border-black pt-4">
		<svg
			viewBox="-10 0 {width + 20} {axis + 60}"
			class="block w-full"
			role="img"
			aria-label="Arc diagram of paragraph references in {graph.regulation}"
			onpointermove={onMove}
			onpointerleave={() => (hovered = null)}
		>
			{#each arcs as a, k (k)}
				<path
					d={arcPath(a.s, a.t)}
					fill="none"
					stroke={a.both ? '#0b7a70' : a.gold ? '#27dac2' : '#000000'}
					stroke-opacity={a.both ? 1 : a.gold ? 0.8 : 0.12}
					stroke-width={a.both ? 2 : 1}
				/>
			{/each}
			<line x1="0" x2={width} y1={axis} y2={axis} stroke="#000000" />
			{#each graph.nodes as n, i (i)}
				{#if !n.gold}
					<line
						x1={x(i)}
						x2={x(i)}
						y1={axis}
						y2={axis + Math.max(2, tickBase - depths[i] * 1.5)}
						stroke="#000000"
						stroke-opacity="0.35"
					/>
				{/if}
			{/each}
			{#each golden as i (i)}
				<rect x={x(i) - 2} y={axis - 4} width="4" height="22" fill="#79F2DE" />
			{/each}
			{#each sections as s (s.i)}
				<text x={x(s.i)} y={axis + 40} font-size="9" fill="#11504b">
					{s.label.replace('Annex ', 'A')}
				</text>
			{/each}
			{#if hovered !== null}
				<line x1={x(hovered)} x2={x(hovered)} y1="0" y2={axis + 24} stroke="#000000" />
			{/if}
		</svg>
		<figcaption
			class="mt-3 grid min-h-12 gap-1 border-t border-black pt-2 text-sm md:grid-cols-[12rem_1fr]"
		>
			{#if hovered !== null}
				{@const n = graph.nodes[hovered]}
				<span class="font-medium tabular-nums"
					>{n.label}, page {n.page}{n.gold ? ', golden' : ''}</span
				>
				<span class="text-cv-ink-800">{n.text}</span>
			{:else}
				<span class="font-medium">Paragraphs in document order</span>
				<span class="text-cv-ink-800">
					Arcs are references between paragraphs. Mint marks are golden paragraphs, dark teal arcs
					join two golden paragraphs. Point at the axis to read a paragraph.
				</span>
			{/if}
		</figcaption>
	</figure>
</div>

<style>
.reggraph-root {
	font-family: "Hanken Grotesk", "Helvetica Neue", Arial, sans-serif;
	font-feature-settings: "ss01";
}
</style>
