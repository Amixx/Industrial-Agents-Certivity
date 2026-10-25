<script lang="ts">
import type { Snippet } from 'svelte';
import { pendingUpdates } from '#lib/api/regulations.ts';
import type { Assessment } from '#lib/api/types.ts';
import { costSummary } from '#lib/report/cost.ts';
import { formatDate } from '#lib/ui/format.ts';
import { page } from '$app/state';

let { assessment, children }: { assessment: Assessment; children?: Snippet } = $props();

const tabs = $derived([
	{ href: `/a/${assessment.id}`, label: 'Requirements' },
	{ href: `/a/${assessment.id}/graph`, label: 'Graph' },
	{ href: `/a/${assessment.id}/exploded`, label: 'Exploded view' },
	{ href: `/a/${assessment.id}/report`, label: 'Report' },
	{ href: `/a/${assessment.id}/coverage`, label: 'Coverage' },
	{
		href: `/a/${assessment.id}/updates`,
		label: 'Updates',
		count: pendingUpdates(assessment).length,
	},
]);

/** The Updates tab stays current on its run pages. */
const isCurrent = (href: string) =>
	page.url.pathname === href || (href.endsWith('/updates') && page.url.pathname.startsWith(href));
</script>

<div class="ui-rule-soft flex flex-wrap items-center gap-x-6 gap-y-2 border-t border-b pt-2 pb-2">
	<a
		href="/a/{assessment.id}"
		class="ui-display max-w-[24ch] truncate text-[1.75rem] hover:text-accent"
	>
		{assessment.caseName ?? 'Untitled spec'}
	</a>
	<div class="flex gap-3 font-mono text-[12px] text-muted tabular-nums">
		<span>#{assessment.id}</span>
		<span>{formatDate(assessment.createdAt)}</span>
		{#if assessment.cost}
			<span title="Model cost of the pipeline run">Run cost {costSummary(assessment.cost)}</span>
		{/if}
	</div>
	<nav class="flex items-baseline gap-5 text-sm">
		{#each tabs as tab (tab.href)}
			<a
				href={tab.href}
				class="flex items-center gap-2 {isCurrent(tab.href) ? 'font-bold' : 'hover:underline'}"
				aria-current={isCurrent(tab.href) ? 'page' : undefined}
			>
				{#if isCurrent(tab.href)}
					<span class="size-2 bg-mark"></span>
				{/if}
				{tab.label}
				{#if 'count' in tab && tab.count}
					<span class="font-mono text-[11.5px] font-normal text-accent tabular-nums"
						>{tab.count}</span
					>
				{/if}
			</a>
		{/each}
	</nav>
	<div class="ml-auto flex items-center gap-3">
		{@render children?.()}
	</div>
</div>
