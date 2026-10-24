<script lang="ts">
import { api } from '#lib/api/client.ts';
import type { Assessment } from '#lib/api/types.ts';
import AssessmentHeader from '#lib/components/AssessmentHeader.svelte';
import { rearLamp } from '#lib/exploded/rearLamp.ts';
import ProcessGraph from '#lib/graph/ProcessGraph.svelte';
import { goto } from '$app/navigation';
import { page } from '$app/state';

let assessment = $state<Assessment | null>(null);
let loaded = $state(false);

/** A part picked in the exploded view arrives as ?part=<id>. */
const part = $derived(rearLamp.parts.find((p) => p.id === page.url.searchParams.get('part')));

$effect(() => {
	const id = page.params.id;
	if (!id) return;
	api.getAssessment(id).then((a) => {
		assessment = a;
		loaded = true;
	});
});
</script>

<svelte:head><title>Graph | sudo</title></svelte:head>

{#if assessment}
	<AssessmentHeader {assessment} />
	<div class="min-h-0 flex-1 overflow-auto pt-6 pb-12">
		<ProcessGraph
			{assessment}
			{part}
			onclearpart={() => goto(page.url.pathname, { replace: true })}
		/>
	</div>
{:else if loaded}
	<p class="pt-6 text-sm">Assessment not found. <a href="/history" class="ui-link">History</a></p>
{/if}
