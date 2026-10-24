<script lang="ts">
import type { Snippet } from 'svelte';

let {
	title,
	meta,
	actions,
	children,
	class: klass = '',
}: {
	title: string;
	meta?: string;
	actions?: Snippet;
	children: Snippet;
	class?: string;
} = $props();
</script>

<section class="flex min-h-0 flex-col {klass}">
	<header class="ui-rule flex items-baseline justify-between gap-2 border-b px-3 py-1.5">
		<h2 class="ui-label font-medium opacity-100">
			{title}
			{#if meta}
				<span class="ui-mono ml-1 opacity-60">{meta}</span>
			{/if}
		</h2>
		{@render actions?.()}
	</header>
	{@render children()}
</section>
