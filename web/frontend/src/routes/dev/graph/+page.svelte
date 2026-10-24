<script lang="ts">
import { onMount } from 'svelte';
import { api } from '#lib/api/client.ts';
import spec from '#lib/api/fixtures/spec.md?raw';
import { regulationIndex } from '#lib/api/regulations.ts';
import type { Assessment } from '#lib/api/types.ts';
import ProcessGraph from '#lib/graph/ProcessGraph.svelte';

let assessment = $state<Assessment | null>(null);
let error = $state<string | null>(null);

onMount(async () => {
	try {
		const latest = (await api.listAssessments()).find((a) => a.status === 'complete');
		assessment = latest ?? (await api.runAssessment(spec, null, () => {}, 'dev-rear-lamp'));
	} catch (e) {
		error = e instanceof Error ? e.message : String(e);
	}
});
</script>

<svelte:head>
	<title>sudo, process graph</title>
	<link rel="preconnect" href="https://fonts.googleapis.com">
	<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous">
	<link
		rel="stylesheet"
		href="https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@300;400;500;600;700;800&display=swap"
	>
</svelte:head>

<div class="graph-root min-h-screen bg-white px-12 pb-16 text-black">
	<header class="flex items-end justify-between border-t-[6px] border-black pt-3 pb-6">
		<div class="flex items-baseline gap-6">
			<h1 class="text-6xl leading-[0.8] font-bold tracking-[-0.05em]">sudo</h1>
			<p class="text-sm font-medium">How the spec reaches the regulations</p>
		</div>
		<p class="text-xs">
			{#if assessment}
				{assessment.caseName ?? assessment.id}, {regulationIndex.length} regulations screened
			{/if}
		</p>
	</header>

	{#if error}
		<p class="border-t-2 border-red-600 pt-2 text-sm font-medium text-red-600">{error}</p>
	{:else if assessment}
		<ProcessGraph {assessment} />
	{:else}
		<p class="border-t border-black pt-2 text-sm">Running the pipeline on the rear lamp spec</p>
	{/if}
</div>

<style>
.graph-root {
	font-family: "Hanken Grotesk", "Helvetica Neue", Arial, sans-serif;
	font-feature-settings: "ss01";
}
</style>
