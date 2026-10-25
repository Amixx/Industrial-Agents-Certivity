<script lang="ts">
import type { RequirementChange } from '#lib/api/types.ts';
import WordDiff from '#lib/ui/WordDiff.svelte';
import type { GraphUpdate } from '#lib/updates/graphDiff.ts';
import {
	changeId,
	changeKinds,
	changeReading,
	paragraphName,
	type Reading,
} from '#lib/updates/run.ts';
import type { ClusterNode } from './model.ts';

let {
	update,
	after,
	node,
	onclose,
	onread,
}: {
	update: GraphUpdate;
	after: boolean;
	/** A paragraph group of the run's regulation, or null for the run's overview. */
	node: ClusterNode | null;
	onclose: () => void;
	onread: (list: Reading[], index: number) => void;
} = $props();

const run = $derived(update.run);
const changes = $derived(node ? (update.changes.get(node.key) ?? []) : run.changes);
const count = (kind: string) => changes.filter((c) => c.change === kind).length;

function read(c: RequirementChange) {
	const list = changes.map((x) => changeReading(run, x)).filter((x): x is Reading => !!x);
	const index = list.findIndex((x) => x.id === changeId(c));
	if (index >= 0) onread(list, index);
}
</script>

{#if !node}
	<div class="label">Update</div>
	<h2 class="mt-2 text-xl leading-tight font-bold">{run.regulation}</h2>
	<p class="font-mono text-[12px] text-muted tabular-nums">
		{run.fromVersion}
		to {run.toVersion}, {after ? 'after the update' : 'as it is'}
	</p>
	<dl class="mt-5 grid grid-cols-3 gap-x-4">
		{#each [
			['Amended', run.stats.amended],
			['New', run.stats.new],
			['Deleted', run.stats.deleted],
		] as const as [label, value] (label)}
			<div class="border-t border-line pt-1">
				<dt class="text-xs">{label}</dt>
				<dd class="text-4xl leading-none font-light text-accent tabular-nums">{value}</dd>
			</div>
		{/each}
	</dl>
	<p class="mt-2 text-xs text-muted">Paragraphs of {run.regulation}</p>
	<p class="mt-5 text-sm leading-snug">
		{count('modified')}
		requirements modified, {count('removed')} removed, {count('added')} added. Lit groups hold them;
		the rest is dimmed.
	</p>
	<p class="mt-4 text-xs leading-snug text-muted">
		Click a lit paragraph group to read its changes on the new version's page.
	</p>
{:else}
	<div class="flex items-baseline justify-between">
		<div class="label">Paragraph group</div>
		<button type="button" class="text-xs underline" onclick={onclose}>Close</button>
	</div>
	<h2 class="mt-2 text-xl leading-tight font-bold">{node.regulation} {node.label}</h2>
	<p class="font-mono text-[12px] text-muted tabular-nums">
		{node.requirements.length}
		requirements {after ? `in ${run.toVersion}` : `in ${run.fromVersion}`}
	</p>
	{#each changeKinds as kind (kind)}
		{@const rows = changes.filter((c) => c.change === kind)}
		{#if rows.length}
			<div class="mt-5 flex items-baseline gap-2 border-b border-line-strong pb-1">
				<span class="text-2xl leading-none font-light text-accent tabular-nums">{rows.length}</span>
				<span class="text-xs font-bold">{kind}</span>
			</div>
			<ol>
				{#each rows as c (changeId(c))}
					<li class="border-b border-line">
						<button
							type="button"
							class="block w-full cursor-pointer py-2 text-left hover:bg-fg/[0.04] disabled:cursor-default"
							disabled={!c.source}
							onclick={() => read(c)}
						>
							<div class="flex items-baseline justify-between gap-2 font-mono text-[12px]">
								<span class="font-bold tabular-nums">{changeId(c)}</span>
								{#if c.source}
									<span class="text-muted tabular-nums">
										{run.toVersion}, p. {c.source.page}, {paragraphName(c.source.paragraph)}
									</span>
								{/if}
							</div>
							<div class="mt-1 text-[13px] leading-snug">
								{#if c.change === 'modified'}
									<WordDiff before={c.oldText} after={c.newText} />
								{:else if c.change === 'removed'}
									<p class="text-muted line-through decoration-1">{c.oldText}</p>
								{:else}
									<p class="border-l-2 border-mark pl-2">{c.newText}</p>
								{/if}
							</div>
						</button>
					</li>
				{/each}
			</ol>
		{/if}
	{/each}
{/if}

<style>
.label {
	font-size: 0.6875rem;
	font-weight: 700;
}
</style>
