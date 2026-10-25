<script lang="ts">
import AssessmentHeader from '#lib/components/AssessmentHeader.svelte';
import { rearLamp } from '#lib/exploded/rearLamp.ts';
import ProcessGraph from '#lib/graph/ProcessGraph.svelte';
import { graphUpdate } from '#lib/updates/graphDiff.ts';
import { goto } from '$app/navigation';
import { page } from '$app/state';

let { data } = $props();
const assessment = $derived(data.assessment);

/** A part picked in the exploded view arrives as ?part=<id>. */
const part = $derived(rearLamp.parts.find((p) => p.id === page.url.searchParams.get('part')));

/** An update run arrives as ?update=<run>: the graph lights what it changes. */
const update = $derived(assessment && data.update ? graphUpdate(assessment, data.update) : null);
let showAfter = $state(false);
</script>

<svelte:head><title>Graph | sudo</title></svelte:head>

{#if assessment}
	<AssessmentHeader {assessment} />
	{#if update}
		<div class="flex items-center gap-4 pt-3">
			<span class="ui-label">Update</span>
			<span class="font-mono text-[12px] tabular-nums">
				{update.run.regulation}
				{update.run.fromVersion}
				to {update.run.toVersion}
			</span>
			<div class="flex rounded-[3px] border border-line-strong p-0.5">
				{#each [
					[false, update.run.fromVersion, 'as it is'],
					[true, update.run.toVersion, update.before ? 'after the update' : 'applied'],
				] as const as [state, version, label] (version)}
					{@const on = state ? showAfter || !update.before : !showAfter && !!update.before}
					<button
						type="button"
						class="flex h-8 cursor-pointer items-baseline gap-2 rounded-[2px] px-3 text-sm disabled:cursor-default {on
							? 'bg-select font-bold text-fg'
							: 'text-muted hover:text-fg'}"
						aria-pressed={on}
						disabled={!state && !update.before}
						onclick={() => (showAfter = state)}
					>
						<span class="self-center font-mono tabular-nums">{version}</span>
						<span class="self-center text-xs font-normal">{label}</span>
					</button>
				{/each}
			</div>
			<a href="/a/{assessment.id}/updates/{update.run.id}" class="ui-link ml-auto text-xs">
				Back to the comparison
			</a>
		</div>
	{/if}
	<div class="min-h-0 flex-1 overflow-auto pt-4 pb-12">
		<ProcessGraph
			{assessment}
			{part}
			{update}
			{showAfter}
			onclearpart={() => goto(page.url.pathname, { replace: true })}
		/>
	</div>
{:else}
	<p class="pt-6 text-sm">Assessment not found. <a href="/history" class="ui-link">History</a></p>
{/if}
