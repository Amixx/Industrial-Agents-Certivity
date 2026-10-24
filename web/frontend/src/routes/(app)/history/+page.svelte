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
		<div class="ui-numeral">1</div>
		<h1 class="mt-2 text-sm font-bold">Saved assessments</h1>
	</div>
	<div class="col-span-2">
		<div class="ui-count text-7xl">{assessments?.length ?? ''}</div>
		<div class="mt-2 text-xs">assessments in total</div>
	</div>

	<div class="col-span-8 min-h-0 overflow-auto pb-10">
		{#if assessments?.length}
			<table class="w-full border-collapse text-left">
				<thead class="sticky top-0 bg-white">
					<tr class="border-b-2 border-black text-xs">
						<th class="pr-4 pb-1.5 font-bold">Case</th>
						<th class="pr-4 pb-1.5 font-bold">Product</th>
						<th class="pr-4 pb-1.5 font-bold">Created</th>
						<th class="pr-4 pb-1.5 font-bold">Regulations</th>
						<th class="pb-1.5 text-right font-bold">Requirements</th>
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
							<td
								class="py-3 text-right text-3xl leading-none font-light text-cv-teal-700 tabular-nums"
							>
								{a.requirements.length}
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		{:else if assessments}
			<p class="text-3xl leading-tight font-light">
				No saved assessments yet. <a href="/" class="ui-link">Start one</a>
			</p>
		{/if}
	</div>
</div>
