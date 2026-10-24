<script lang="ts">
import type { Assessment } from '#lib/api/types.ts';
import { buildGraph, columns, type GraphNode, groupLabels } from './model.ts';
import NodeDetail from './NodeDetail.svelte';

let { assessment }: { assessment: Assessment } = $props();

const graph = $derived(buildGraph(assessment));
const byId = $derived(new Map(graph.nodes.map((n) => [n.id, n])));

let hovered = $state<string | null>(null);
let selected = $state<string | null>(null);

const focus = $derived(hovered ?? selected);
const active = $derived(focus ? graph.connected(focus) : null);
const selectedNode = $derived(selected ? (byId.get(selected) ?? null) : null);

const dim = (id: string) => (active && !active.has(id) ? 'dim' : '');
const edgeOn = (from: string, to: string) => !!active && active.has(from) && active.has(to);

const included = $derived(assessment.regulations.filter((r) => r.included));

function pick(node: GraphNode) {
	selected = selected === node.id ? null : node.id;
}

const PAD_TOP = 8;
</script>

<div class="grid grid-cols-[minmax(0,1fr)_340px] gap-x-6">
	<div class="min-w-0 overflow-x-auto">
		<ol
			class="relative grid border-t border-black pt-2 text-xs"
			style:width="{graph.width}px"
			style:height="52px"
		>
			{#each [
				['1', 'Spec', columns.spec],
				['2', 'Product profile', columns.facet],
				['3', 'Regulations', columns.regulation],
				['4', 'Paragraphs', columns.cluster],
			] as const as [n, label, col] (n)}
				<li class="absolute top-2" style:left="{col.x}px" style:width="{col.w}px">
					<div class="text-3xl leading-none font-light text-cv-teal-700">{n}</div>
					<div class="mt-1 font-bold">{label}</div>
				</li>
			{/each}
		</ol>

		<div
			class="relative mt-4"
			style:width="{graph.width}px"
			style:height="{graph.height + PAD_TOP}px"
		>
			<svg
				class="pointer-events-none absolute inset-0"
				width={graph.width}
				height={graph.height + PAD_TOP}
				aria-hidden="true"
			>
				<g transform="translate(0 {PAD_TOP})">
					{#each graph.edges as e (e.id)}
						<path
							d={e.path}
							class="edge {e.kind}"
							class:on={edgeOn(e.from, e.to)}
							class:off={active && !edgeOn(e.from, e.to)}
							stroke-width={e.width}
						/>
					{/each}
				</g>
			</svg>

			{#each graph.headers as h (h.group)}
				<div class="label absolute" style:left="{columns.facet.x}px" style:top="{h.y + PAD_TOP}px">
					{groupLabels[h.group]}
				</div>
			{/each}
			<div class="label absolute" style:left="{columns.regulation.x}px" style:top="{PAD_TOP}px">
				Included, {included.length}
			</div>


			{#each graph.nodes as node (node.id)}
				<button
					type="button"
					class="node {node.kind} {dim(node.id)}"
					class:selected={selected === node.id}
					class:hot={!!active && focus !== node.id && active.has(node.id) && node.kind !== 'spec'}
					style:left="{node.x}px"
					style:top="{node.y + PAD_TOP}px"
					style:width="{node.w}px"
					style:height="{node.h}px"
					onmouseenter={() => (hovered = node.id)}
					onmouseleave={() => (hovered = null)}
					onfocus={() => (hovered = node.id)}
					onblur={() => (hovered = null)}
					onclick={() => pick(node)}
				>
					{#if node.kind === 'spec'}
						<span class="block text-[11px]">{assessment.caseName ?? 'Spec'}</span>
						<span class="mt-1 block text-xl leading-tight font-bold">
							{assessment.profile.productType.split(/\s+[—-]\s+/)[0]}
						</span>
						<span class="mt-auto block text-[11px] leading-snug">
							{assessment.profile.parts.length}
							parts<br>
							{assessment.profile.functions.length}
							functions<br>
							{assessment.profile.materials.length}
							materials
						</span>
					{:else if node.kind === 'facet'}
						{#if node.group === 'materials'}
							<span class="truncate leading-tight font-medium">{node.label}</span>
							<span class="truncate text-[10.5px] leading-tight text-cv-ink-800">
								{node.detail}
							</span>
						{:else if node.group === 'product'}
							<span class="truncate leading-tight font-medium">{node.label}</span>
							<span class="truncate text-[10.5px] leading-tight text-cv-ink-800">
								{node.detail}
							</span>
						{:else}
							<span class="line-clamp-2 leading-tight font-medium">{node.label}</span>
						{/if}
					{:else if node.kind === 'regulation'}
						{#if node.decision.included}
							<span class="flex items-baseline justify-between">
								<span class="text-sm font-bold">{node.decision.regulation}</span>
								<span class="text-3xl leading-none font-light text-cv-teal-700 tabular-nums">
									{node.decision.requirementCount}
								</span>
							</span>
							<span class="mt-1 line-clamp-2 text-[11px] leading-tight">
								{node.decision.title}
							</span>
						{:else}
							<span class="flex gap-2 truncate text-[11px] leading-none">
								<span class="w-12 shrink-0 font-bold">{node.decision.regulation}</span>
								<span class="truncate">{node.decision.reason}</span>
							</span>
						{/if}
					{:else}
						<span class="flex items-center justify-between gap-2 text-[11px]">
							<span class="truncate font-medium">{node.label}</span>
							<span class="tabular-nums">{node.requirements.length}</span>
						</span>
					{/if}
				</button>
			{/each}
		</div>
	</div>

	<aside
		class="sticky top-6 max-h-[calc(100vh-3rem)] self-start overflow-y-auto border-t border-black pt-2"
	>
		<NodeDetail node={selectedNode} {assessment} onclose={() => (selected = null)} />
	</aside>
</div>

<style>
.label {
	font-size: 0.6875rem;
	font-weight: 700;
	line-height: 1;
}
.edge {
	fill: none;
	stroke: var(--color-cv-ink-950);
	stroke-opacity: 0.13;
	transition:
		stroke-opacity 120ms,
		stroke 120ms;
}
.edge.spec {
	stroke-opacity: 0.18;
}
.edge.reason {
	stroke-dasharray: 3 3;
	stroke-opacity: 0.3;
}
.edge.cluster {
	stroke: var(--color-cv-teal-700);
	stroke-opacity: 0.22;
}
.edge.on {
	stroke: var(--color-cv-teal-500);
	stroke-opacity: 0.75;
}
.edge.reason.on {
	stroke: var(--color-cv-ink-800);
	stroke-opacity: 0.7;
}
.edge.off {
	stroke-opacity: 0.04;
}
.reason {
	z-index: 1;
	border: 1px solid var(--color-cv-ink-950);
	border-radius: 2px;
	background: white;
	padding: 6px 8px;
	font-size: 11px;
	line-height: 1.35;
	pointer-events: none;
}
.node {
	position: absolute;
	display: flex;
	flex-direction: column;
	justify-content: center;
	overflow: hidden;
	border: 1px solid var(--color-cv-ink-950);
	border-radius: 2px;
	background: white;
	padding: 0 8px;
	text-align: left;
	font-size: 12px;
	color: black;
	transition: opacity 120ms;
	cursor: pointer;
}
.node.spec {
	justify-content: flex-start;
	border-width: 2px 0 0;
	border-radius: 0;
	padding: 8px 0 0;
}
.node.regulation:not(.muted) {
	justify-content: flex-start;
	border-top-width: 2px;
	padding-top: 6px;
}
.node.muted {
	border-color: transparent;
	color: color-mix(in srgb, var(--color-cv-ink-950) 55%, white);
	padding: 0 4px;
}
.node.muted:hover,
.node.muted.hot,
.node.muted.selected {
	color: var(--color-cv-ink-950);
	border-color: var(--color-cv-ink-950);
}
.node:hover,
.node.hot {
	background: var(--color-cv-mint-50);
}
.node.spec:hover,
.node.spec.hot {
	background: white;
}
.node.selected {
	outline: 2px solid var(--color-cv-teal-400);
	outline-offset: 1px;
	background: var(--color-cv-mint-50);
}
.node.dim {
	opacity: 0.25;
}
.node:focus-visible {
	outline: 2px solid var(--color-cv-teal-700);
	outline-offset: 1px;
}
</style>
