<script lang="ts">
import { fly } from 'svelte/transition';
import { pdfUrl } from '#lib/api/regulations.ts';
import type { Requirement } from '#lib/api/types.ts';
import SourceViewer from '#lib/components/SourceViewer.svelte';

let {
	list,
	index = $bindable(),
	onclose,
}: {
	/** The requirements the drawer steps through, in the order the panel lists them. */
	list: Requirement[];
	index: number;
	onclose: () => void;
} = $props();

const req = $derived(list[index]);
const url = $derived(pdfUrl(req.source));

function onkeydown(e: KeyboardEvent) {
	if (e.key === 'Escape') onclose();
	else if (e.key === 'ArrowRight' && index < list.length - 1) index++;
	else if (e.key === 'ArrowLeft' && index > 0) index--;
}
</script>

<svelte:window {onkeydown} />

<aside
	class="fixed inset-y-0 right-0 z-30 flex w-[min(46rem,52vw)] flex-col border-l border-line-strong bg-canvas"
	transition:fly={{ x: 120, duration: 260, opacity: 0 }}
	aria-label="Source paragraph"
>
	<header class="flex items-start gap-4 border-b border-line px-5 pt-4 pb-3">
		<div class="min-w-0 flex-1">
			<div class="flex items-baseline gap-3 font-mono text-[12px] text-muted tabular-nums">
				<span class="font-bold text-fg">{req.id}</span>
				<span>{req.source.regulation} {req.source.version}</span>
				<span>p. {req.source.page}</span>
				<span>§ {req.source.paragraph}</span>
			</div>
			<p class="mt-1.5 line-clamp-2 text-[14px] leading-snug">{req.text}</p>
		</div>
		<div class="flex shrink-0 items-center gap-1">
			{#if list.length > 1}
				<button
					type="button"
					class="ui-toggle"
					disabled={index === 0}
					onclick={() => index--}
					aria-label="Previous requirement"
				>
					Prev
				</button>
				<span class="px-1 font-mono text-[12px] text-muted tabular-nums">
					{index + 1}
					of {list.length}
				</span>
				<button
					type="button"
					class="ui-toggle"
					disabled={index === list.length - 1}
					onclick={() => index++}
					aria-label="Next requirement"
				>
					Next
				</button>
			{/if}
			<button type="button" class="ui-btn ml-2" onclick={onclose}>Close</button>
		</div>
	</header>
	{#if url}
		<SourceViewer
			{url}
			page={req.source.page}
			highlight={{ paragraph: req.source.paragraph, text: req.text }}
			label={req.id}
			class="min-h-0 w-full flex-1"
		/>
	{:else}
		<p class="p-5 text-sm">No PDF on file for {req.source.regulation} {req.source.version}.</p>
	{/if}
</aside>
