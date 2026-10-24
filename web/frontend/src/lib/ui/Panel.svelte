<script lang="ts">
import type { Snippet } from 'svelte';

let {
	title,
	index,
	meta,
	actions,
	children,
	class: klass = '',
}: {
	title: string;
	index?: number;
	meta?: string;
	actions?: Snippet;
	children: Snippet;
	class?: string;
} = $props();
</script>

<section class="flex min-h-0 flex-col {klass}">
	<header class="ui-section flex items-end justify-between gap-2 pb-3">
		<div>
			{#if index !== undefined}
				<div class="ui-numeral">{index}</div>
			{/if}
			<h2 class="mt-2 text-sm font-bold">{title}</h2>
			{#if meta}
				<div class="text-xs">{meta}</div>
			{/if}
		</div>
		{@render actions?.()}
	</header>
	{@render children()}
</section>
