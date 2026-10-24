<script lang="ts">
	import '#lib/ui/theme.css';
	import { page } from '$app/state';
	import Wordmark from '#lib/ui/Wordmark.svelte';

	let { children } = $props();

	const nav = [
		{ href: '/', label: 'New assessment' },
		{ href: '/history', label: 'History' }
	];
</script>

<svelte:head>
	<link rel="preconnect" href="https://fonts.googleapis.com" />
	<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous" />
	<link
		rel="stylesheet"
		href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap"
	/>
</svelte:head>

<div class="ui-app flex h-screen flex-col">
	<header class="ui-rule flex items-baseline justify-between border-b px-4 py-2">
		<Wordmark />
		<nav class="flex gap-4 text-xs">
			{#each nav as item (item.href)}
				<a
					href={item.href}
					class="ui-link tracking-wide uppercase"
					class:font-semibold={page.url.pathname === item.href}>{item.label}</a
				>
			{/each}
		</nav>
	</header>
	<div class="flex min-h-0 flex-1 flex-col">
		{@render children()}
	</div>
</div>
