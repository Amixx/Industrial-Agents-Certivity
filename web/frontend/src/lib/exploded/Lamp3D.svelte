<script lang="ts">
import { onMount, untrack } from 'svelte';
import type { PartCoverage } from '#lib/graph/model.ts';
import { goto } from '$app/navigation';
import type { LampScene } from './lamp3d.ts';
import PartHoverCard from './PartHoverCard.svelte';
import type { ExplodedAssembly } from './rearLamp.ts';

let {
	assembly,
	coverage,
	graphHref,
	requirementsHref,
	initialPart = null,
}: {
	assembly: ExplodedAssembly;
	coverage: Record<string, PartCoverage>;
	graphHref: (id: string) => string;
	/** The requirement list filtered to one part. */
	requirementsHref: (id: string) => string;
	initialPart?: string | null;
} = $props();

let host: HTMLDivElement | undefined = $state();
let scene: LampScene | null = $state(null);
let explode = $state(0);
let selectedId: string | null = $state(untrack(() => initialPart));
let lit = $state(false);
let hoveredId: string | null = $state(null);
/** Pointer position inside the model area, for the hover card. */
let cursor = $state({ x: 0, y: 0 });

const pad = (n: number) => String(n + 1).padStart(2, '0');
const selected = $derived(assembly.parts.find((p) => p.id === selectedId) ?? null);
const hoveredIndex = $derived(assembly.parts.findIndex((p) => p.id === hoveredId));
const hoveredCoverage = $derived(hoveredId ? coverage[hoveredId] : undefined);

function track(e: PointerEvent) {
	if (!host || !hoveredId) return;
	const rect = host.getBoundingClientRect();
	cursor = { x: e.clientX - rect.left, y: e.clientY - rect.top };
}

onMount(() => {
	let disposed = false;
	let created: LampScene | null = null;
	// three.js is only needed here, so it loads with this view.
	import('./lamp3d.ts').then(({ createLampScene }) => {
		if (disposed || !host) return;
		created = createLampScene(
			host,
			assembly.parts.map((p, i) => ({ id: p.id, number: pad(i), name: p.name })),
			// A part clicked in the model opens its regulations in the graph; empty space clears.
			(id) => {
				if (id) goto(graphHref(id));
				else selectedId = null;
			},
			(id) => (hoveredId = id),
		);
		scene = created;
		setTimeout(() => (explode = 1), 500);
	});
	return () => {
		disposed = true;
		created?.dispose();
	};
});

$effect(() => scene?.setExplode(explode));
$effect(() => scene?.setSelected(selectedId));
$effect(() => scene?.setLit(lit));
</script>

<svelte:window onpointermove={track} />

<div class="ui-grid min-h-0 flex-1 pt-6 pb-6">
	<aside class="col-span-3 flex min-h-0 flex-col overflow-auto">
		<div class="ui-section pb-3">
			<span class="ui-label">Exploded view, 3D</span>
			<p class="mt-1 text-xs">
				Drag to rotate. Scroll to zoom. Click a part to see its regulations in the graph.
			</p>
		</div>
		<ul class="border-t-2 border-line">
			{#each assembly.parts as part, i (part.id)}
				<li class="ui-rule-soft border-b">
					<button
						type="button"
						class="grid w-full cursor-pointer grid-cols-[2.5rem_1fr] items-baseline py-2.5 pl-5 text-left hover:bg-fg/[0.04] {selectedId ===
						part.id
							? 'ui-row-selected'
							: ''}"
						style:--ui-marker-top="0.95rem"
						onclick={() => (selectedId = selectedId === part.id ? null : part.id)}
					>
						<span class="text-xl leading-none font-light text-accent tabular-nums">{pad(i)}</span>
						<span class="text-sm font-bold">{part.name}</span>
					</button>
				</li>
			{/each}
		</ul>
		{#if selected}
			<dl class="space-y-3 pt-5 text-xs">
				<div>
					<dt class="ui-label">Material</dt>
					<dd class="text-sm leading-snug">{selected.material}</dd>
				</div>
				<div>
					<dt class="ui-label">Check</dt>
					<dd class="text-sm leading-snug">{selected.check}</dd>
				</div>
				<div class="flex gap-4">
					<a href={requirementsHref(selected.id)} class="ui-link text-xs"
						>Show its {coverage[selected.id]?.requirements ?? 0} requirements</a
					>
					<a href={graphHref(selected.id)} class="ui-link text-xs">Show in graph</a>
				</div>
			</dl>
		{/if}
	</aside>

	<div class="col-span-9 flex min-h-0 flex-col">
		<div bind:this={host} class="lamp3d relative min-h-0 flex-1 cursor-grab active:cursor-grabbing">
			{#if !scene}
				<p class="absolute inset-0 grid place-items-center text-xs">Loading model</p>
			{/if}
			{#if hoveredId && hoveredCoverage}
				<PartHoverCard
					number={pad(hoveredIndex)}
					name={assembly.parts[hoveredIndex].name}
					coverage={hoveredCoverage}
					x={cursor.x}
					y={cursor.y}
					width={host?.clientWidth ?? 0}
					height={host?.clientHeight ?? 0}
				/>
			{/if}
		</div>
		<div class="ui-section flex flex-wrap items-center gap-x-6 gap-y-3">
			<label class="flex items-center gap-3 text-xs font-bold">
				<span>Assembled</span>
				<input
					type="range"
					min="0"
					max="1"
					step="0.01"
					bind:value={explode}
					class="w-56 accent-accent"
					aria-label="Explode distance"
				>
				<span>Exploded</span>
			</label>
			<div class="flex gap-1">
				<button
					type="button"
					class="ui-toggle {lit ? '' : 'ui-toggle-on'}"
					onclick={() => (lit = false)}
				>
					Lamp off
				</button>
				<button
					type="button"
					class="ui-toggle {lit ? 'ui-toggle-on' : ''}"
					onclick={() => (lit = true)}
				>
					Lamp on
				</button>
			</div>
			<button
				type="button"
				class="ui-link ml-auto cursor-pointer text-xs"
				onclick={() => scene?.resetView()}
			>
				Reset view
			</button>
		</div>
	</div>
</div>
