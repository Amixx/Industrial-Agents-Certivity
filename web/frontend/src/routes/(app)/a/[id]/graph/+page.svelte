<script lang="ts">
import AssessmentHeader from '#lib/components/AssessmentHeader.svelte';
import { assemblyFor } from '#lib/exploded/assemblies.ts';
import ProcessGraph from '#lib/graph/ProcessGraph.svelte';
import { goto } from '$app/navigation';
import { page } from '$app/state';

let { data } = $props();
const assessment = $derived(data.assessment);

/** A part picked in the exploded view arrives as ?part=<id>. */
const part = $derived(
	assessment &&
		assemblyFor(assessment)?.parts.find((p) => p.id === page.url.searchParams.get('part')),
);
</script>

<svelte:head><title>Graph | sudo</title></svelte:head>

{#if assessment}
	<AssessmentHeader {assessment} />
	<div class="min-h-0 flex-1 overflow-auto pt-4 pb-12">
		<ProcessGraph
			{assessment}
			{part}
			onclearpart={() => goto(page.url.pathname, { replace: true })}
		/>
	</div>
{:else}
	<p class="pt-6 text-sm">Assessment not found. <a href="/history" class="ui-link">History</a></p>
{/if}
