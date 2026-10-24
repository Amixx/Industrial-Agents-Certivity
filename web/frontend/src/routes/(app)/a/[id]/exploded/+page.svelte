<script lang="ts">
import { api } from '#lib/api/client.ts';
import type { Assessment } from '#lib/api/types.ts';
import AssessmentHeader from '#lib/components/AssessmentHeader.svelte';
import ExplodedView from '#lib/exploded/ExplodedView.svelte';
import Lamp3D from '#lib/exploded/Lamp3D.svelte';
import { rearLamp } from '#lib/exploded/rearLamp.ts';
import { page } from '$app/state';

let assessment = $state<Assessment | null>(null);
let loaded = $state(false);

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

{#if assessment}
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
		<Lamp3D assembly={rearLamp} />
	{:else}
		<ExplodedView assembly={rearLamp} />
	{/if}
{:else if loaded}
	<p class="pt-6 text-sm">Assessment not found. <a href="/history" class="ui-link">History</a></p>
{/if}
