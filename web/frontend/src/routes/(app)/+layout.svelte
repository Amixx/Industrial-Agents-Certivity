<script lang="ts">
import '#lib/ui/theme.css';
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
		href="https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@300;400;500;600;700;800&display=swap"
	>
</svelte:head>

<div class="ui-app ui-gutter flex h-screen flex-col">
	<header class="flex items-end justify-between border-t-[6px] border-black pt-4 pb-5">
		<Wordmark />
		<nav class="flex gap-8 text-sm font-medium">
			{#each nav as item (item.href)}
				{@const active = page.url.pathname === item.href}
				<a
					href={item.href}
					class="relative hover:underline {active ? 'font-bold' : ''}"
					aria-current={active ? 'page' : undefined}
				>
					{#if active}
						<span
							class="absolute top-1.5 -left-4 size-2 bg-cv-mint-300 outline outline-1 outline-black"
						></span>
					{/if}
					{item.label}
				</a>
			{/each}
		</nav>
	</header>
	<div class="flex min-h-0 flex-1 flex-col">
		{@render children()}
	</div>
</div>
