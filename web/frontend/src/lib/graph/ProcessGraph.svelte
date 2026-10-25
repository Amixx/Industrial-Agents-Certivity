<script lang="ts">
import type { Assessment } from '#lib/api/types.ts';
import {
	buildGraph,
	columns,
	type GraphNode,
	groupLabels,
	type PartFocus,
	partFacets,
} from './model.ts';
import NodeDetail from './NodeDetail.svelte';
import PartDetail from './PartDetail.svelte';

let {
	assessment,
	part = null,
	onclearpart,
}: { assessment: Assessment; part?: PartFocus | null; onclearpart?: () => void } = $props();

const graph = $derived(buildGraph(assessment));
const byId = $derived(new Map(graph.nodes.map((n) => [n.id, n])));

let hovered = $state<string | null>(null);
let selected = $state<string | null>(null);

const focus = $derived(hovered ?? selected);
const focusFacets = $derived(part ? partFacets(graph, part) : []);
const focusIds = $derived(new Set(focusFacets.map((f) => f.id)));
/** With a part in focus and nothing hovered or picked, everything its facets reach stays lit. */
const partActive = $derived(
	focusFacets.length ? new Set(focusFacets.flatMap((f) => [...graph.connected(f.id)])) : null,
);
const active = $derived(focus ? graph.connected(focus) : partActive);
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
			class="relative grid border-t border-line pt-2 text-xs"
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
					<div class="text-3xl leading-none font-light text-accent">{n}</div>
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
					class:selected={selected === node.id || (!selected && focusIds.has(node.id))}
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
							<span class="truncate text-[10.5px] leading-tight text-muted">
								{node.detail}
							</span>
						{:else if node.group === 'product'}
							<span class="truncate leading-tight font-medium">{node.label}</span>
							<span class="truncate text-[10.5px] leading-tight text-muted">
								{node.detail}
							</span>
						{:else}
							<span class="line-clamp-2 leading-tight font-medium">{node.label}</span>
						{/if}
					{:else if node.kind === 'regulation'}
						{#if node.decision.included}
							<span class="flex items-baseline justify-between">
								<span class="text-sm font-bold">{node.decision.regulation}</span>
								<span class="text-3xl leading-none font-light text-accent tabular-nums">
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
		class="sticky top-6 max-h-[calc(100vh-3rem)] self-start overflow-y-auto border-t border-line pt-2"
	>
		{#if part && !selectedNode}
			<PartDetail {part} facets={focusFacets} {assessment} onclose={() => onclearpart?.()} />
		{:else}
			<NodeDetail node={selectedNode} {assessment} onclose={() => (selected = null)} />
		{/if}
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
	stroke: var(--color-fg);
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
	stroke: var(--color-accent);
	stroke-opacity: 0.22;
}
.edge.on {
	stroke: var(--color-mark);
	stroke-opacity: 0.75;
}
.edge.reason.on {
	stroke: var(--color-muted);
	stroke-opacity: 0.7;
}
.edge.off {
	stroke-opacity: 0.04;
}
.reason {
	z-index: 1;
	border: 1px solid var(--color-line-strong);
	border-radius: 2px;
	background: var(--color-panel);
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
	border: 1px solid var(--color-line-strong);
	border-radius: 2px;
	background: var(--color-panel);
	padding: 0 8px;
	text-align: left;
	font-size: 12px;
	color: var(--color-fg);
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
	color: var(--color-faint);
	padding: 0 4px;
}
.node.muted:hover,
.node.muted.hot,
.node.muted.selected {
	color: var(--color-fg);
	border-color: var(--color-line-strong);
}
.node:hover,
.node.hot {
	background: var(--color-select);
}
.node.spec:hover,
.node.spec.hot {
	background: var(--color-panel);
}
.node.selected {
	outline: 2px solid var(--color-accent);
	outline-offset: 1px;
	background: var(--color-select);
}
.node.dim {
	opacity: 0.25;
}
.node:focus-visible {
	outline: 2px solid var(--color-accent);
	outline-offset: 1px;
}
</style>
