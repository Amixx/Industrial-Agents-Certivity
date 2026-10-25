<script lang="ts">
import { onMount, untrack } from 'svelte';
import type { PartCoverage } from '#lib/graph/model.ts';
import { goto } from '$app/navigation';
import type { LampScene } from './lamp3d.ts';
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
		<ul class="border-t-2 border-black">
			{#each assembly.parts as part, i (part.id)}
				<li class="ui-rule-soft border-b">
					<button
						type="button"
						class="grid w-full cursor-pointer grid-cols-[2.5rem_1fr] items-baseline py-2.5 pl-5 text-left hover:bg-black/[0.03] {selectedId ===
						part.id
							? 'ui-row-selected'
							: ''}"
						style:--ui-marker-top="0.95rem"
						onclick={() => (selectedId = selectedId === part.id ? null : part.id)}
					>
						<span class="text-xl leading-none font-light text-cv-teal-700 tabular-nums"
							>{pad(i)}</span
						>
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
				{@const part = assembly.parts[hoveredIndex]}
				<div
					class="hover-card pointer-events-none absolute z-10 w-60 border border-black bg-white px-3 pt-2 pb-2.5"
					style:left="{Math.min(cursor.x + 16, (host?.clientWidth ?? 0) - 256)}px"
					style:top="{cursor.y + 16}px"
					style:translate={cursor.y > (host?.clientHeight ?? 0) / 2
						? '0 calc(-100% - 32px)'
						: undefined}
				>
					<div class="flex items-baseline gap-2">
						<span class="text-sm leading-none font-light text-cv-teal-700 tabular-nums">
							{pad(hoveredIndex)}
						</span>
						<span class="text-sm font-bold">{part.name}</span>
					</div>
					<dl class="mt-2 grid grid-cols-3 gap-x-3 border-t border-black pt-1">
						<div class="flex flex-col-reverse">
							<dt class="mt-1 text-[10.5px]">Regulations</dt>
							<dd class="text-2xl leading-none font-light text-cv-teal-700 tabular-nums">
								{hoveredCoverage.regulations.length}
							</dd>
						</div>
						<div class="flex flex-col-reverse">
							<dt class="mt-1 text-[10.5px]">Requirements</dt>
							<dd class="text-2xl leading-none font-light text-cv-teal-700 tabular-nums">
								{hoveredCoverage.requirements}
							</dd>
						</div>
						<div class="flex flex-col-reverse">
							<dt class="mt-1 text-[10.5px]">Paragraphs</dt>
							<dd class="text-2xl leading-none font-light text-cv-teal-700 tabular-nums">
								{hoveredCoverage.paragraphs}
							</dd>
						</div>
					</dl>
					{#if hoveredCoverage.regulations.length}
						<ul class="mt-2 space-y-0.5 border-t border-black pt-1.5 text-[11px]">
							{#each hoveredCoverage.regulations as reg (reg.regulation)}
								<li class="flex justify-between gap-2">
									<span class="font-bold">{reg.regulation}</span>
									<span class="tabular-nums">
										{reg.requirements.length
											? `${reg.requirements.length} requirements`
											: 'named in the selection reason'}
									</span>
								</li>
							{/each}
						</ul>
					{:else}
						<p class="mt-2 border-t border-black pt-1.5 text-[11px]">
							No regulation mentions this part.
						</p>
					{/if}
					<p class="mt-2 text-[11px] text-cv-ink-800">Click to open it in the graph.</p>
				</div>
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
					class="w-56 accent-black"
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

<style>
.lamp3d :global(.lamp3d-label) {
	display: flex;
	align-items: baseline;
	gap: 0.375rem;
	padding: 0 0.25rem;
	font-size: 11px;
	font-weight: 700;
	white-space: nowrap;
	background: white;
	cursor: pointer;
	pointer-events: auto;
	transition: opacity 120ms linear;
}
.lamp3d :global(.lamp3d-label-no) {
	color: var(--color-cv-teal-700);
	font-weight: 300;
	font-variant-numeric: tabular-nums;
}
.lamp3d :global(.lamp3d-label-on) {
	outline: 1px solid black;
	border-left: 0.25rem solid var(--color-cv-mint-300);
}
</style>
