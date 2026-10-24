<script lang="ts">
import { api } from '#lib/api/client.ts';
import type { Assessment } from '#lib/api/types.ts';
import AssessmentHeader from '#lib/components/AssessmentHeader.svelte';
import ProcessGraph from '#lib/graph/ProcessGraph.svelte';
import { page } from '$app/state';

let assessment = $state<Assessment | null>(null);
let loaded = $state(false);

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
		<ProcessGraph {assessment} />
	</div>
{:else if loaded}
	<p class="pt-6 text-sm">Assessment not found. <a href="/history" class="ui-link">History</a></p>
{/if}
