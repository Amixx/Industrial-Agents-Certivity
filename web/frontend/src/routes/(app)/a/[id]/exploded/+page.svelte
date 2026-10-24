<script lang="ts">
import { api } from '#lib/api/client.ts';
import type { Assessment } from '#lib/api/types.ts';
import AssessmentHeader from '#lib/components/AssessmentHeader.svelte';
import ExplodedView from '#lib/exploded/ExplodedView.svelte';
import { rearLamp } from '#lib/exploded/rearLamp.ts';
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

<svelte:head><title>Exploded view | sudo</title></svelte:head>

{#if assessment}
	<AssessmentHeader {assessment} />
	<ExplodedView assembly={rearLamp} />
{:else if loaded}
	<p class="pt-6 text-sm">Assessment not found. <a href="/history" class="ui-link">History</a></p>
{/if}
