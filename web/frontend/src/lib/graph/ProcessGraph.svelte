<script lang="ts">
import { cubicOut } from 'svelte/easing';
import { Tween } from 'svelte/motion';
import type { Assessment, Requirement } from '#lib/api/types.ts';
import type { GraphUpdate, GroupStatus } from '#lib/updates/graphDiff.ts';
import { changeReading, type Reading } from '#lib/updates/run.ts';
import ChangeDetail from './ChangeDetail.svelte';
import {
	buildGraph,
	type ClusterNode,
	columns,
	type GraphNode,
	groupLabels,
	type PartFocus,
	partFacets,
} from './model.ts';
import NodeDetail from './NodeDetail.svelte';
import PartDetail from './PartDetail.svelte';
import PdfDrawer from './PdfDrawer.svelte';

let {
	assessment: base,
	part = null,
	onclearpart,
	update = null,
	showAfter = false,
}: {
	assessment: Assessment;
	part?: PartFocus | null;
	onclearpart?: () => void;
	/** Diff mode: an update run's changes lit on the graph. */
	update?: GraphUpdate | null;
	/** In diff mode, the assessment as it would be after the update. */
	showAfter?: boolean;
} = $props();

/** In diff mode, the before or after state of the assessment. */
const after = $derived(!!update && (showAfter || !update.before));
const assessment = $derived(
	update ? (after ? update.after : (update.before ?? update.after)) : base,
);
const graph = $derived(
	buildGraph(assessment, update ? { [update.run.regulation]: update.pinned } : {}),
);

/** A cluster's status in diff mode: lit when the update touches it; a new group is hidden
 * before the update, a removed one is an outline after it. */
function statusOf(node: GraphNode): GroupStatus | null {
	if (!update || node.kind !== 'cluster' || node.regulation !== update.run.regulation) return null;
	return update.status.get(node.key) ?? 'same';
}
/** A group the update adds, before it is applied: a dashed placeholder. */
const ghost = (node: GraphNode) => statusOf(node) === 'new' && !after;

/** "+10", "−2", "4 modified": what the update does to a group (or, with no key, to the whole
 * regulation). */
function delta(key?: string) {
	if (!update) return [];
	const list = key === undefined ? update.run.changes : (update.changes.get(key) ?? []);
	const n = (k: string) => list.filter((c) => c.change === k).length;
	return [
		n('added') ? `+${n('added')}` : '',
		n('removed') ? `−${n('removed')}` : '',
		n('modified') ? (key === undefined ? `~${n('modified')}` : `${n('modified')} modified`) : '',
	].filter(Boolean);
}
/** Lit in diff mode: the run's regulation with its facets, and the groups the update touches. */
const diffActive = $derived.by(() => {
	if (!update) return null;
	const lit = graph.nodes.filter((n) => {
		const st = statusOf(n);
		return st && st !== 'same';
	});
	const regulation = [...graph.connected(`r:${update.run.regulation}`)].filter((id) => {
		const node = byId.get(id);
		return node?.kind !== 'cluster';
	});
	return new Set([...regulation, ...lit.flatMap((n) => [...graph.connected(n.id)])]);
});
const regulationCount = new Tween(0, { duration: 900, easing: cubicOut });
$effect(() => {
	const n = update
		? (assessment.regulations.find((d) => d.regulation === update.run.regulation)
				?.requirementCount ?? 0)
		: 0;
	regulationCount.set(n, { duration: regulationCount.current === 0 ? 0 : 900 });
});
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
const active = $derived(focus ? graph.connected(focus) : (partActive ?? diffActive));
const selectedNode = $derived(selected ? (byId.get(selected) ?? null) : null);

const dim = (id: string) => (active && !active.has(id) ? 'dim' : '');
const edgeOn = (from: string, to: string) => !!active && active.has(from) && active.has(to);

const included = $derived(assessment.regulations.filter((r) => r.included));

/** The requirements open in the PDF drawer, and which one is showing. */
let reading = $state<{ list: Requirement[]; index: number } | null>(null);

function read(list: Requirement[], r: Requirement) {
	reading = { list, index: Math.max(0, list.indexOf(r)) };
}

/** The changes of a lit group, on their new paragraphs. */
function readChanges(node: ClusterNode) {
	if (!update) return;
	const run = update.run;
	const list = (update.changes.get(node.key) ?? [])
		.map((c) => changeReading(run, c))
		.filter((x): x is Reading => !!x);
	if (list.length) reading = { list, index: 0 };
}

function pick(node: GraphNode) {
	selected = selected === node.id ? null : node.id;
	const st = statusOf(node);
	if (node.kind === 'cluster' && selected && st && st !== 'same') return readChanges(node);
	// A paragraph group opens straight to its first requirement's source.
	if (node.kind === 'cluster' && selected && node.requirements.length)
		read(node.requirements, node.requirements[0]);
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
					{#each graph.edges as e (update ? `${e.id}:${after}` : e.id)}
						{@const target = byId.get(e.to)}
						{@const st = target ? statusOf(target) : null}
						<path
							d={e.path}
							class="edge {e.kind}"
							class:on={edgeOn(e.from, e.to)}
							class:off={active && !edgeOn(e.from, e.to)}
							class:changed={st === 'changed'}
							class:new={st === 'new' && after}
							class:pending={target ? ghost(target) : false}
							class:draw={!!st && st !== 'same' && !(target && ghost(target))}
							pathLength={st && st !== 'same' && !(target && ghost(target)) ? 1 : undefined}
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
				{@const st = statusOf(node)}
				<button
					type="button"
					class="node {node.kind} {dim(node.id)} {st ? `diff-${st}` : ''}"
					class:ghost={ghost(node)}
					class:gone={st === 'removed' && after}
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
						<span class="block text-[12px]">{assessment.caseName ?? 'Spec'}</span>
						<span class="mt-1 block text-xl leading-tight font-bold">
							{assessment.profile.productType.split(/\s+[—-]\s+/)[0]}
						</span>
						<span class="mt-auto block text-[12px] leading-snug">
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
							<span class="truncate text-[11.5px] leading-tight text-muted">
								{node.detail}
							</span>
						{:else if node.group === 'product'}
							<span class="truncate leading-tight font-medium">{node.label}</span>
							<span class="truncate text-[11.5px] leading-tight text-muted">
								{node.detail}
							</span>
						{:else}
							<span class="line-clamp-2 leading-tight font-medium">{node.label}</span>
						{/if}
					{:else if node.kind === 'regulation'}
						{#if node.decision.included}
							{@const updating = update?.run.regulation === node.decision.regulation}
							<span class="flex items-baseline justify-between">
								<span class="text-sm font-bold">{node.decision.regulation}</span>
								<span class="text-3xl leading-none font-light text-accent tabular-nums">
									{updating ? Math.round(regulationCount.current) : node.decision.requirementCount}
								</span>
							</span>
							{#if updating && update}
								<span
									class="version mt-1 flex items-baseline gap-1.5 font-mono text-[12px] tabular-nums"
								>
									<span class:now={!after}>{update.run.fromVersion}</span>
									<span class="text-faint">to</span>
									<span class:now={after}>{update.run.toVersion}</span>
									<span class="ml-auto font-bold text-accent">{delta().join(' ')}</span>
								</span>
							{:else}
								<span class="mt-1 line-clamp-2 text-[12px] leading-tight">
									{node.decision.title}
								</span>
							{/if}
						{:else}
							<span class="flex gap-2 truncate text-[12px] leading-none">
								<span class="w-12 shrink-0 font-bold">{node.decision.regulation}</span>
								<span class="truncate">{node.decision.reason}</span>
							</span>
						{/if}
					{:else}
						<span class="flex items-center justify-between gap-2 text-[12px]">
							<span class="truncate font-medium">{node.label}</span>
							{#if st && st !== 'same'}
								<span class="ml-auto font-mono text-[11px] font-bold text-accent">
									{st === 'new' && !after
										? `${delta(node.key).join(' ')} in ${update?.run.toVersion}`
										: delta(node.key).join(' ')}
								</span>
							{/if}
							{#if st === 'removed' && after}
								<span class="font-mono text-[11px] text-muted">removed</span>
							{/if}
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
		{#if update && (!selectedNode || statusOf(selectedNode))}
			<ChangeDetail
				{update}
				{after}
				node={selectedNode?.kind === 'cluster' ? selectedNode : null}
				onclose={() => (selected = null)}
				onread={(list, index) => (reading = { list, index })}
			/>
		{:else if part && !selectedNode}
			<div style:view-transition-name="part-card">
				<PartDetail
					{part}
					facets={focusFacets}
					{assessment}
					onclose={() => onclearpart?.()}
					onread={read}
				/>
			</div>
		{:else}
			<NodeDetail
				node={selectedNode}
				{assessment}
				onclose={() => (selected = null)}
				onread={read}
			/>
		{/if}
	</aside>
</div>

{#if reading}
	<PdfDrawer list={reading.list} bind:index={reading.index} onclose={() => (reading = null)} />
{/if}

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
	font-size: 12px;
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
	font-size: 13px;
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
.node.diff-changed:not(.dim),
.node.diff-new:not(.dim) {
	border-color: var(--color-mark);
	border-width: 2px;
}
.node.diff-new {
	border-left-width: 3px;
}
.node.diff-removed.gone {
	border-style: dashed;
	background: transparent;
	color: var(--color-muted);
}
.node.cluster {
	transition:
		opacity 300ms,
		top 600ms cubic-bezier(0.2, 0.7, 0.2, 1),
		height 600ms cubic-bezier(0.2, 0.7, 0.2, 1),
		border-color 300ms;
}
.node.regulation {
	transition:
		opacity 120ms,
		top 600ms cubic-bezier(0.2, 0.7, 0.2, 1),
		height 600ms cubic-bezier(0.2, 0.7, 0.2, 1);
}
.node.ghost {
	border-style: dashed;
	border-color: var(--color-mark);
	background: transparent;
}
.node.ghost .tabular-nums:last-child {
	display: none;
}
.version span {
	color: var(--color-faint);
	transition: color 400ms;
}
.version .now {
	color: var(--color-fg);
	font-weight: 700;
}
.edge.changed,
.edge.new {
	stroke: var(--color-mark);
	stroke-opacity: 0.8;
}
.edge.changed.off,
.edge.new.off {
	stroke-opacity: 0.04;
}
.edge.pending {
	stroke: var(--color-mark);
	stroke-opacity: 0.6;
	stroke-dasharray: 3 4;
}
.edge.draw {
	stroke-dasharray: 1;
	animation: draw 800ms cubic-bezier(0.4, 0, 0.2, 1) both;
}
@keyframes draw {
	from {
		stroke-dashoffset: 1;
	}
	to {
		stroke-dashoffset: 0;
	}
}
@media (prefers-reduced-motion: reduce) {
	.edge.draw {
		animation: none;
	}
}
.node:focus-visible {
	outline: 2px solid var(--color-accent);
	outline-offset: 1px;
}
</style>
