<script lang="ts">
import { api } from '#lib/api/client.ts';
import type { Assessment } from '#lib/api/types.ts';
import AssessmentHeader from '#lib/components/AssessmentHeader.svelte';
import { assemblyFor } from '#lib/exploded/assemblies.ts';
import Exploded3D from '#lib/exploded/Exploded3D.svelte';
import ExplodedView from '#lib/exploded/ExplodedView.svelte';
import { buildGraph, partCoverage, partFacets } from '#lib/graph/model.ts';
import { page } from '$app/state';

let assessment = $state<Assessment | null>(null);
let loaded = $state(false);

const assembly = $derived(assessment && assemblyFor(assessment));

/** What each part covers, counted the same way the graph highlights it. */
const coverage = $derived.by(() => {
	if (!assessment || !assembly) return {};
	const graph = buildGraph(assessment);
	const { requirements } = assessment;
	return Object.fromEntries(
		assembly.parts.map((p) => [p.id, partCoverage(partFacets(graph, p), requirements)]),
	);
});

const mode = $derived(page.url.searchParams.get('view') === 'scroll' ? 'scroll' : '3d');

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

{#if assessment && !assembly}
	<AssessmentHeader {assessment} />
	<p class="pt-6 text-sm">There is no exploded view for this product yet.</p>
{:else if assessment && assembly}
	<AssessmentHeader {assessment}>
		<div class="flex gap-1">
			<a href="?view=3d" class="ui-toggle flex items-center {mode === '3d' ? 'ui-toggle-on' : ''}">
				3D
			</a>
			<a
				href="?view=scroll"
				class="ui-toggle flex items-center {mode === 'scroll' ? 'ui-toggle-on' : ''}"
			>
				Scroll
			</a>
		</div>
	</AssessmentHeader>
	{#if mode === '3d'}
		<!-- A new scene when the product changes, since the model is built once. -->
		{#key assembly}
			<Exploded3D
				{assembly}
				{coverage}
				graphHref={(id) => `/a/${assessment?.id}/graph?part=${id}`}
				requirementsHref={(id) => `/a/${assessment?.id}?part=${id}`}
				initialPart={page.url.searchParams.get('part')}
			/>
		{/key}
	{:else}
		<ExplodedView {assembly} />
	{/if}
{:else if loaded}
	<p class="pt-6 text-sm">Assessment not found. <a href="/history" class="ui-link">History</a></p>
{/if}
