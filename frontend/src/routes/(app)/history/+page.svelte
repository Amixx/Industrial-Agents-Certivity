<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '#lib/api/client.ts';
	import type { Assessment } from '#lib/api/types.ts';
	import { formatDate } from '#lib/ui/format.ts';

	let assessments: Assessment[] | null = $state(null);

	onMount(async () => {
		assessments = await api.listAssessments();
	});
</script>

<svelte:head><title>History · sudo</title></svelte:head>

<div class="ui-rule flex items-baseline justify-between border-b px-4 py-2">
	<span class="ui-label font-medium opacity-100">Saved assessments</span>
	<span class="ui-mono text-xs opacity-70">{assessments?.length ?? ''}</span>
</div>

<div class="min-h-0 flex-1 overflow-auto">
	{#if assessments?.length}
		<table class="w-full border-collapse text-left">
			<thead class="sticky top-0 bg-cv-mint-50">
				<tr class="ui-rule ui-label border-b">
					<th class="px-4 py-1.5 font-medium">Case</th>
					<th class="px-4 py-1.5 font-medium">Product</th>
					<th class="px-4 py-1.5 font-medium">Created</th>
					<th class="px-4 py-1.5 font-medium">Regulations</th>
					<th class="px-4 py-1.5 text-right font-medium">Requirements</th>
				</tr>
			</thead>
			<tbody>
				{#each assessments as a (a.id)}
					<tr class="ui-rule-soft border-b align-top hover:bg-white">
						<td class="px-4 py-2">
							<a href="/a/{a.id}" class="ui-mono ui-link font-medium">{a.caseName ?? 'Untitled spec'}</a>
							<span class="ui-mono ml-2 text-[11px] opacity-60">#{a.id}</span>
						</td>
						<td class="px-4 py-2">{a.profile.productType}</td>
						<td class="ui-mono px-4 py-2 text-xs whitespace-nowrap">{formatDate(a.createdAt)}</td>
						<td class="ui-mono px-4 py-2 text-xs">
							{a.regulations
								.filter((r) => r.included)
								.map((r) => `${r.regulation.replace('UN ', '')} ${r.version}`)
								.join(' · ')}
						</td>
						<td class="ui-mono px-4 py-2 text-right">{a.requirements.length}</td>
					</tr>
				{/each}
			</tbody>
		</table>
	{:else if assessments}
		<p class="p-4 opacity-60">No saved assessments yet. <a href="/" class="ui-link">Start one</a></p>
	{/if}
</div>
