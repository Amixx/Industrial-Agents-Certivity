<script lang="ts">
import type { Assessment } from '#lib/api/types.ts';
import { type GraphNode, groupLabels } from './model.ts';

let {
	node,
	assessment,
	onclose,
}: { node: GraphNode | null; assessment: Assessment; onclose: () => void } = $props();

const included = $derived(assessment.regulations.filter((r) => r.included));
</script>

{#if !node || node.kind === 'spec'}
	<div class="label">Overview</div>
	<p class="mt-2 text-sm leading-snug">
		The spec becomes a product profile. Each facet links to the regulations whose requirements
		mention it; edge width is the number of matching requirements.
	</p>
	<dl class="mt-6 grid grid-cols-2 gap-x-4 gap-y-4">
		<div class="border-t border-line pt-1">
			<dt class="text-xs">Included</dt>
			<dd class="text-4xl leading-none font-light text-accent tabular-nums">
				{included.length}
			</dd>
		</div>
		<div class="col-span-2 border-t border-line pt-1">
			<dt class="text-xs">Requirements</dt>
			<dd class="text-4xl leading-none font-light text-accent tabular-nums">
				{assessment.requirements.length}
			</dd>
		</div>
	</dl>
	<p class="mt-6 text-xs leading-snug">
		Hover a node to trace its path. Click a paragraph group to list its requirements. Dashed edges
		link a facet to a regulation through the selection reason only.
	</p>
{:else}
	<div class="flex items-baseline justify-between">
		<div class="label">
			{#if node.kind === 'facet'}
				{groupLabels[node.group]}
			{:else if node.kind === 'regulation'}
				Included regulation
			{:else}
				Paragraph group
			{/if}
		</div>
		<button type="button" class="text-xs underline" onclick={onclose}>Close</button>
	</div>

	{#if node.kind === 'facet'}
		<h2 class="mt-2 text-xl leading-tight font-bold">{node.label}</h2>
		{#if node.detail}
			<p class="mt-1 text-sm">{node.detail}</p>
		{/if}
		<ul class="mt-5">
			{#each node.links as link (link.regulation)}
				<li class="flex items-baseline justify-between border-t border-line py-2 text-sm">
					<span class="font-bold">{link.regulation}</span>
					<span class="text-xs">
						{#if link.requirementIds.length}
							{link.requirementIds.length}
							requirements mention it
						{:else}
							named in the selection reason
						{/if}
					</span>
				</li>
			{:else}
				<li class="border-t border-line py-2 text-sm">No regulation mentions this facet.</li>
			{/each}
		</ul>
	{:else if node.kind === 'regulation'}
		<h2 class="mt-2 text-xl leading-tight font-bold">{node.decision.regulation}</h2>
		<p class="text-sm">{node.decision.title}</p>
		{#if node.decision.version}
			<p class="mt-1 text-xs">Version {node.decision.version}</p>
		{/if}
		<div class="mt-5 border-t border-line pt-1">
			<div class="text-xs">{node.decision.included ? 'Why it applies' : 'Why it is excluded'}</div>
			<p class="mt-1 text-sm leading-snug">{node.decision.reason}</p>
		</div>
		{#if node.decision.included}
			<div class="mt-5 border-t border-line pt-1">
				<div class="text-xs">Requirements</div>
				<div class="text-4xl leading-none font-light text-accent tabular-nums">
					{node.decision.requirementCount}
				</div>
			</div>
		{/if}
	{:else}
		<h2 class="mt-2 text-xl leading-tight font-bold">
			{node.regulation}
			{node.label}
		</h2>
		<p class="text-xs">{node.requirements.length} requirements</p>
		<ol class="mt-4">
			{#each node.requirements as r (r.id)}
				<li class="border-t border-line py-2">
					<div class="flex items-baseline justify-between gap-2 text-[11px]">
						<span class="font-bold tabular-nums">{r.id}</span>
						<span class="text-muted">
							{r.source.regulation}
							{r.source.version}, p. {r.source.page}, § {r.source.paragraph}
						</span>
					</div>
					<p class="mt-1 text-[13px] leading-snug">{r.text}</p>
				</li>
			{/each}
		</ol>
	{/if}
{/if}

<style>
.label {
	font-size: 0.6875rem;
	font-weight: 700;
}
</style>
