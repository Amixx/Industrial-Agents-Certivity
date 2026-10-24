<script lang="ts">
import { onMount } from 'svelte';
import type { LampScene } from './lamp3d.ts';
import type { ExplodedAssembly } from './rearLamp.ts';

let { assembly }: { assembly: ExplodedAssembly } = $props();

let host: HTMLDivElement | undefined = $state();
let scene: LampScene | null = $state(null);
let explode = $state(0);
let selectedId: string | null = $state(null);
let lit = $state(false);

const pad = (n: number) => String(n + 1).padStart(2, '0');
const selected = $derived(assembly.parts.find((p) => p.id === selectedId) ?? null);

onMount(() => {
	let disposed = false;
	let created: LampScene | null = null;
	// three.js is only needed here, so it loads with this view.
	import('./lamp3d.ts').then(({ createLampScene }) => {
		if (disposed || !host) return;
		created = createLampScene(
			host,
			assembly.parts.map((p, i) => ({ id: p.id, number: pad(i), name: p.name })),
			(id) => (selectedId = id === selectedId ? null : id),
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

<div class="ui-grid min-h-0 flex-1 pt-6 pb-6">
	<aside class="col-span-3 flex min-h-0 flex-col overflow-auto">
		<div class="ui-section pb-3">
			<span class="ui-label">Exploded view, 3D</span>
			<p class="mt-1 text-xs">Drag to rotate. Scroll to zoom. Click a part to isolate it.</p>
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
			</dl>
		{/if}
	</aside>

	<div class="col-span-9 flex min-h-0 flex-col">
		<div bind:this={host} class="lamp3d relative min-h-0 flex-1 cursor-grab active:cursor-grabbing">
			{#if !scene}
				<p class="absolute inset-0 grid place-items-center text-xs">Loading model</p>
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
