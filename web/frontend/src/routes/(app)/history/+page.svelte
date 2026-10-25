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

<svelte:head><title>History | sudo</title></svelte:head>

<div class="ui-grid ui-section min-h-0 flex-1">
	<div class="col-span-2">
		<span class="ui-label">History</span>
		<h1 class="ui-display mt-3 text-[2.5rem]">Saved <i>assessments</i></h1>
	</div>
	<div class="col-span-2">
		<div class="ui-count text-7xl">{assessments?.length ?? ''}</div>
		<div class="ui-label mt-2">In total</div>
	</div>

	<div class="col-span-8 min-h-0 overflow-auto pb-10">
		{#if assessments?.length}
			<table class="w-full border-collapse text-left">
				<thead class="sticky top-0 bg-canvas">
					<tr class="border-b border-line-strong">
						<th class="pr-4 pb-1.5 ui-label table-cell">Case</th>
						<th class="pr-4 pb-1.5 ui-label table-cell">Product</th>
						<th class="pr-4 pb-1.5 ui-label table-cell">Created</th>
						<th class="pr-4 pb-1.5 ui-label table-cell">Regulations</th>
						<th class="pb-1.5 text-right ui-label table-cell">Requirements</th>
					</tr>
				</thead>
				<tbody>
					{#each assessments as a (a.id)}
						<tr class="ui-rule-soft border-b align-top">
							<td class="py-3 pr-4">
								<a href="/a/{a.id}" class="text-base font-bold whitespace-nowrap hover:underline"
									>{a.caseName ?? 'Untitled spec'}</a
								>
								<div class="text-xs tabular-nums">#{a.id}</div>
							</td>
							<td class="py-3 pr-4 leading-snug">{a.profile.productType}</td>
							<td class="py-3 pr-4 text-xs whitespace-nowrap tabular-nums">
								{formatDate(a.createdAt)}
							</td>
							<td class="py-3 pr-4 text-xs tabular-nums">
								{#each a.regulations.filter((r) => r.included) as r (r.regulation)}
									<div class="whitespace-nowrap">
										<span class="font-bold">{r.regulation.replace('UN ', '')}</span>
										{r.version}
									</div>
								{/each}
							</td>
							<td class="py-3 text-right text-3xl leading-none font-light text-accent tabular-nums">
								{a.requirements.length}
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		{:else if assessments}
			<p class="text-3xl leading-tight font-light">
				No saved assessments yet. <a href="/new" class="ui-link">Start one</a>
			</p>
		{/if}
	</div>
</div>
