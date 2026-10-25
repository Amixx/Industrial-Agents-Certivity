<script lang="ts">
import type { Assessment } from '#lib/api/types.ts';
import { type FacetNode, type PartFocus, partCoverage } from './model.ts';

let {
	part,
	facets,
	assessment,
	onclose,
}: { part: PartFocus; facets: FacetNode[]; assessment: Assessment; onclose: () => void } = $props();

const coverage = $derived(partCoverage(facets, assessment.requirements));
const regulations = $derived(coverage.regulations);
</script>

<div class="flex items-baseline justify-between">
	<div class="label">Part, from the exploded view</div>
	<button type="button" class="text-xs underline" onclick={onclose}>Close</button>
</div>
<h2 class="mt-2 text-xl leading-tight font-bold">{part.name}</h2>
<p class="text-xs">
	{regulations.length}
	regulations, {coverage.requirements} requirements, {coverage.paragraphs} paragraphs
</p>

{#each regulations as reg (reg.regulation)}
	<section class="mt-5">
		<div class="flex items-baseline justify-between border-t-2 border-line pt-1">
			<span class="text-sm font-bold">{reg.regulation}</span>
			<span class="text-xs">
				{#if reg.requirements.length}
					{reg.requirements.length}
					requirements
				{:else}
					named in the selection reason
				{/if}
			</span>
		</div>
		<ol>
			{#each reg.requirements as r (r.id)}
				<li class="border-t border-line py-2">
					<div class="flex items-baseline justify-between gap-2 text-[11px]">
						<span class="font-bold tabular-nums">{r.id}</span>
						<span class="text-muted">
							{r.source.version}, p. {r.source.page}, § {r.source.paragraph}
						</span>
					</div>
					<p class="mt-1 text-[13px] leading-snug">{r.text}</p>
				</li>
			{/each}
		</ol>
	</section>
{:else}
	<p class="mt-5 border-t border-line py-2 text-sm">No regulation mentions this part.</p>
{/each}

<style>
.label {
	font-size: 0.6875rem;
	font-weight: 700;
}
</style>
