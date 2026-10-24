<script lang="ts">
	import { onMount } from 'svelte';
	import { Select } from 'bits-ui';
	import { app } from '#lib/app.svelte.ts';

	onMount(() => app.demo());

	const selectedUrl = $derived(app.selected ? app.pdfUrl(app.selected.source) : null);
</script>

<svelte:head>
	<title>Datasheet</title>
	<link rel="preconnect" href="https://fonts.googleapis.com" />
	<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous" />
	<link
		rel="stylesheet"
		href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap"
	/>
</svelte:head>

<div class="flex h-screen flex-col bg-cv-mint-50 font-['IBM_Plex_Sans'] text-sm text-cv-ink-800">
	<header class="flex items-baseline justify-between border-b border-cv-ink-800 px-4 py-2">
		<div class="flex items-baseline gap-3">
			<h1 class="font-['IBM_Plex_Mono'] text-2xl font-medium tracking-tight">sudo</h1>
			<span class="text-[11px] tracking-wide uppercase opacity-60">in collaboration with Certivity</span>
			<span class="ml-4 font-['IBM_Plex_Mono'] text-xs opacity-70">{app.result?.case_id ?? ''}</span>
		</div>
		<a href="/v" class="text-xs underline">All variants</a>
	</header>

	<form
		class="grid grid-cols-[14rem_1fr_9rem_auto] items-stretch gap-px border-b border-cv-ink-800 bg-cv-ink-800/30"
		onsubmit={(e) => {
			e.preventDefault();
			app.submit();
		}}
	>
		<div class="bg-cv-mint-50 p-2">
			<div class="mb-1 text-[10px] tracking-wider uppercase opacity-70">Case</div>
			<Select.Root
				type="single"
				value={app.selectedCase}
				onValueChange={(v) => app.loadCase(v)}
				items={app.cases.map((c) => ({ value: c, label: c }))}
			>
				<Select.Trigger
					class="flex h-7 w-full items-center justify-between border border-cv-ink-800 bg-white px-2 font-['IBM_Plex_Mono'] text-xs"
				>
					{app.selectedCase || 'Select case'}
					<span aria-hidden="true">▾</span>
				</Select.Trigger>
				<Select.Portal>
					<Select.Content
						sideOffset={2}
						class="z-50 max-h-64 w-(--bits-select-anchor-width) overflow-auto border border-cv-ink-800 bg-white font-['IBM_Plex_Mono'] text-xs text-cv-ink-800"
					>
						<Select.Viewport>
							{#each app.cases as c (c)}
								<Select.Item
									value={c}
									label={c}
									class="cursor-default px-2 py-1 data-highlighted:bg-cv-mint-300 data-selected:font-medium"
								>
									{c}
								</Select.Item>
							{/each}
						</Select.Viewport>
					</Select.Content>
				</Select.Portal>
			</Select.Root>
			<label class="mt-2 block text-[10px] tracking-wider uppercase opacity-70">
				Spec file
				<input
					type="file"
					accept=".md,.txt,text/*"
					onchange={(e) => app.setSpecFile(e.currentTarget.files?.[0])}
					class="mt-0.5 block w-full text-xs normal-case file:mr-2 file:border file:border-cv-ink-800 file:bg-white file:px-2 file:py-0.5"
				/>
			</label>
		</div>

		<label class="flex flex-col bg-cv-mint-50 p-2">
			<span class="mb-1 text-[10px] tracking-wider uppercase opacity-70">Product spec</span>
			<textarea
				bind:value={app.spec}
				rows="6"
				class="min-h-0 flex-1 resize-none border border-cv-ink-800 bg-white p-2 font-['IBM_Plex_Mono'] text-xs leading-snug"
			></textarea>
		</label>

		<div class="flex flex-col bg-cv-mint-50 p-2">
			<span class="mb-1 text-[10px] tracking-wider uppercase opacity-70">Exploded view</span>
			<div class="flex min-h-0 flex-1 items-center justify-center border border-cv-ink-800 bg-white">
				{#if app.imageUrl}
					<img src={app.imageUrl} alt="Exploded view" class="max-h-24 max-w-full object-contain" />
				{:else}
					<span class="text-xs opacity-50">none</span>
				{/if}
			</div>
			<input
				type="file"
				accept="image/*"
				onchange={(e) => app.setImageFile(e.currentTarget.files?.[0])}
				class="mt-1 block w-full text-xs file:mr-2 file:border file:border-cv-ink-800 file:bg-white file:px-2 file:py-0.5"
			/>
		</div>

		<div class="flex flex-col justify-end gap-2 bg-cv-mint-50 p-2">
			<button
				disabled={app.loading}
				class="h-8 border border-cv-ink-800 bg-cv-ink-800 px-4 text-xs font-medium tracking-wider text-cv-mint-50 uppercase hover:bg-cv-ink-950 disabled:opacity-60"
			>
				{app.loading ? 'Running…' : 'Run'}
			</button>
			<button
				type="button"
				disabled={!app.result}
				onclick={() => app.download()}
				class="h-8 border border-cv-ink-800 px-4 text-xs tracking-wider uppercase hover:bg-cv-mint-300 disabled:opacity-40"
			>
				Download JSON
			</button>
		</div>
	</form>

	{#if app.error}
		<p class="border-b border-cv-ink-800 bg-white px-4 py-1 font-['IBM_Plex_Mono'] text-xs">
			ERROR {app.error}
		</p>
	{/if}

	<div class="flex min-h-0 flex-1">
		<main class="min-w-0 flex-1 overflow-auto">
			{#if app.byRegulation.length}
				<div class="flex flex-wrap border-b border-cv-ink-800">
					{#each app.byRegulation as g (g.regulation)}
						<div class="border-r border-cv-ink-800/30 px-3 py-1.5 text-xs">
							<span class="font-['IBM_Plex_Mono'] font-medium">{g.regulation}</span>
							<span class="opacity-70">{g.title}</span>
							<span class="ml-1 font-['IBM_Plex_Mono'] font-medium">×{g.count}</span>
						</div>
					{/each}
				</div>
				<table class="w-full border-collapse text-left">
					<thead class="sticky top-0 bg-cv-mint-50">
						<tr class="border-b border-cv-ink-800 text-[10px] tracking-wider uppercase">
							<th class="w-20 px-3 py-1 font-medium">ID</th>
							<th class="px-3 py-1 font-medium">Requirement</th>
							<th class="w-20 px-3 py-1 font-medium">Version</th>
							<th class="w-14 px-3 py-1 font-medium">Page</th>
							<th class="w-24 px-3 py-1 font-medium">Para.</th>
						</tr>
					</thead>
					{#each app.byRegulation as g (g.regulation)}
						<tbody>
							<tr class="border-b border-cv-ink-800/30 bg-cv-mint-300/40">
								<th colspan="5" class="px-3 py-1 text-left text-xs font-semibold">
									<span class="font-['IBM_Plex_Mono']">{g.regulation}</span>
									— {g.title}
									<span class="font-['IBM_Plex_Mono'] font-normal opacity-70">({g.count})</span>
								</th>
							</tr>
							{#each g.requirements as req (req.id)}
								{@const url = app.pdfUrl(req.source)}
								<tr
									onclick={() => app.select(req.id)}
									class="cursor-pointer border-b border-cv-ink-800/20 align-top hover:bg-white {app.selectedId ===
									req.id
										? 'bg-white outline outline-1 -outline-offset-1 outline-cv-ink-800'
										: ''}"
								>
									<td class="px-3 py-1.5 font-['IBM_Plex_Mono'] text-xs whitespace-nowrap">
										{req.id}
									</td>
									<td class="px-3 py-1.5 leading-snug">{req.text}</td>
									<td class="px-3 py-1.5 font-['IBM_Plex_Mono'] text-xs whitespace-nowrap">
										{req.source.version}
									</td>
									<td class="px-3 py-1.5 font-['IBM_Plex_Mono'] text-xs">
										{#if url}
											<a
												href={url}
												target="_blank"
												rel="noreferrer"
												onclick={(e) => e.stopPropagation()}
												class="underline">{req.source.page}</a
											>
										{:else}
											{req.source.page}
										{/if}
									</td>
									<td class="px-3 py-1.5 font-['IBM_Plex_Mono'] text-xs whitespace-nowrap">
										{req.source.paragraph ?? ''}
									</td>
								</tr>
							{/each}
						</tbody>
					{/each}
				</table>
			{:else}
				<p class="p-4 opacity-60">{app.loading ? 'Running…' : 'No results yet.'}</p>
			{/if}
		</main>

		<aside class="flex w-[38%] min-w-80 flex-col border-l border-cv-ink-800 bg-white">
			{#if app.selected && selectedUrl}
				<div class="border-b border-cv-ink-800 px-3 py-1.5 font-['IBM_Plex_Mono'] text-xs">
					{app.selected.id} · {app.selected.source.regulation}
					{app.selected.source.version} · p.{app.selected.source.page}
				</div>
				{#key selectedUrl}
					<iframe src={selectedUrl} title="Source page" class="min-h-0 flex-1 border-0"></iframe>
				{/key}
			{:else}
				<p class="p-4 opacity-60">Select a requirement to view its source page.</p>
			{/if}
		</aside>
	</div>
</div>
