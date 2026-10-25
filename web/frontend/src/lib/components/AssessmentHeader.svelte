<script lang="ts">
import type { Snippet } from 'svelte';
import type { Assessment } from '#lib/api/types.ts';
import { costSummary } from '#lib/report/cost.ts';
import { formatDate } from '#lib/ui/format.ts';
import { page } from '$app/state';

let { assessment, children }: { assessment: Assessment; children?: Snippet } = $props();

const tabs = $derived([
	{ href: `/a/${assessment.id}`, label: 'Requirements' },
	{ href: `/a/${assessment.id}/graph`, label: 'Graph' },
	{ href: `/a/${assessment.id}/exploded`, label: 'Exploded view' },
]);
</script>

<div class="ui-grid ui-section items-end pb-4">
	<div class="col-span-3 text-xs">
		<div class="font-bold">Assessment</div>
		<div class="tabular-nums">{formatDate(assessment.createdAt)}</div>
		<div class="tabular-nums">#{assessment.id}</div>
		{#if assessment.cost}
			<div class="tabular-nums" title="Model cost of the pipeline run">
				Run cost {costSummary(assessment.cost)}
			</div>
		{/if}
	</div>
	<a
		href="/a/{assessment.id}"
		class="col-span-4 truncate text-4xl leading-none font-bold tracking-tight hover:underline"
	>
		{assessment.caseName ?? 'Untitled spec'}
	</a>
	<div class="col-span-5 flex items-center justify-end gap-3">
		{@render children?.()}
	</div>
</div>

<nav class="ui-rule-soft flex items-baseline gap-6 border-b pb-2 text-sm">
	{#each tabs as tab (tab.href)}
		<a
			href={tab.href}
			class="flex items-center gap-2 {page.url.pathname === tab.href
				? 'font-bold'
				: 'hover:underline'}"
			aria-current={page.url.pathname === tab.href ? 'page' : undefined}
		>
			{#if page.url.pathname === tab.href}
				<span class="size-2 bg-cv-mint-300 outline outline-1 outline-black"></span>
			{/if}
			{tab.label}
		</a>
	{/each}
	<a href="/report/{assessment.id}" class="ml-auto text-xs hover:underline">Printable report</a>
</nav>
