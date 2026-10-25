<script lang="ts">
import '#lib/ui/theme.css';
import { colorScheme } from '#lib/ui/colorScheme.svelte.ts';
import Wordmark from '#lib/ui/Wordmark.svelte';
import { page } from '$app/state';

let { children } = $props();

const nav = [
	{ href: '/', label: 'New assessment' },
	{ href: '/history', label: 'History' },
];
</script>

<svelte:head>
	<link rel="preconnect" href="https://fonts.googleapis.com">
	<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous">
	<link
		rel="stylesheet"
		href="https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@300;400;500;600;700;800&family=Instrument+Serif:ital@0;1&family=JetBrains+Mono:wght@400;500&display=swap"
	>
</svelte:head>

<div class="ui-app flex h-screen flex-col">
	<header class="ui-gutter flex items-center justify-between border-b border-line py-3">
		<Wordmark />
		<nav class="flex items-center gap-1">
			{#each nav as item (item.href)}
				{@const active = page.url.pathname === item.href}
				<a
					href={item.href}
					class="flex h-8 items-center rounded-button px-3 text-xs font-medium {active
						? 'bg-select text-fg'
						: 'text-muted hover:bg-fg/5 hover:text-fg'}"
					aria-current={active ? 'page' : undefined}
				>
					{item.label}
				</a>
			{/each}
			<button
				type="button"
				class="ml-3 flex h-8 cursor-pointer items-center rounded-button border border-line px-3 font-mono text-[10.5px] tracking-[0.08em] text-muted uppercase hover:border-line-strong hover:text-fg"
				onclick={() => colorScheme.toggle()}
			>
				{colorScheme.current === 'dark' ? 'Light' : 'Dark'}
			</button>
		</nav>
	</header>
	<div class="ui-gutter flex min-h-0 flex-1 flex-col pt-5">
		{@render children()}
	</div>
</div>
