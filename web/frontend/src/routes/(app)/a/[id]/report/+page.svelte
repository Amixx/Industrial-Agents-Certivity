<script lang="ts">
import { api } from '#lib/api/client.ts';
import type { Assessment } from '#lib/api/types.ts';
import AssessmentHeader from '#lib/components/AssessmentHeader.svelte';
import Report from '#lib/report/Report.svelte';
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

<svelte:head><title>Report | sudo</title></svelte:head>

{#if assessment}
	<AssessmentHeader {assessment}>
		<a href="/report/{assessment.id}" class="ui-toggle flex items-center">Print / Save as PDF</a>
	</AssessmentHeader>
	<div class="relative min-h-0 flex-1 overflow-auto bg-black/[0.04] px-4">
		<Report {assessment} inApp />
	</div>
{:else if loaded}
	<p class="pt-6 text-sm">Assessment not found. <a href="/history" class="ui-link">History</a></p>
{/if}
