<script lang="ts">
	import { onMount, tick } from 'svelte';
	import { Select } from 'bits-ui';
	import { app } from '#lib/app.svelte.ts';

	onMount(() => app.demo());

	let filter = $state('');
	let filterEl: HTMLInputElement | undefined = $state();
	let listEl: HTMLDivElement | undefined = $state();
	let collapsed: Record<string, boolean> = $state({});

	const selectedUrl = $derived(app.selected ? app.pdfUrl(app.selected.source) : null);
	const total = $derived(app.result?.requirements.length ?? 0);

	const rows = $derived.by(() => {
		const q = filter.trim().toLowerCase();
		return app.byRegulation
			.flatMap((g) => g.requirements)
			.filter(
				(r) =>
					!q ||
					[r.id, r.text, r.source.regulation, r.source.paragraph ?? ''].some((s) =>
						s.toLowerCase().includes(q)
					)
			);
	});
	const cursor = $derived(rows.findIndex((r) => r.id === app.selectedId));

	$effect(() => {
		if (app.result && !app.selectedId && rows.length) app.select(rows[0].id);
	});

	async function move(to: number) {
		if (!rows.length) return;
		const i = Math.max(0, Math.min(rows.length - 1, to));
		app.select(rows[i].id);
		await tick();
		listEl?.querySelector(`[data-id="${rows[i].id}"]`)?.scrollIntoView({ block: 'nearest' });
	}

	function onKey(e: KeyboardEvent) {
		if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
			e.preventDefault();
			app.submit();
			return;
		}
		const t = e.target as HTMLElement;
		if (t.closest('input, textarea, select, [role="listbox"], [role="combobox"]')) {
			if (e.key === 'Escape') t.blur();
			return;
		}
		if (e.metaKey || e.ctrlKey || e.altKey) return;
		const actions: Record<string, () => void> = {
			j: () => move(cursor + 1),
			ArrowDown: () => move(cursor + 1),
			k: () => move(cursor - 1),
			ArrowUp: () => move(cursor - 1),
			g: () => move(0),
			Home: () => move(0),
			G: () => move(rows.length - 1),
			End: () => move(rows.length - 1),
			'/': () => filterEl?.focus(),
			o: () => selectedUrl && window.open(selectedUrl, '_blank', 'noreferrer'),
			Enter: () => selectedUrl && window.open(selectedUrl, '_blank', 'noreferrer')
		};
		const action = actions[e.key];
		if (action) {
			e.preventDefault();
			action();
		}
	}
</script>

<svelte:head>
	<title>Workbench</title>
	<link rel="preconnect" href="https://fonts.googleapis.com" />
	<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous" />
	<link
		rel="stylesheet"
		href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Space+Grotesk:wght@400;500;700&display=swap"
	/>
</svelte:head>

<svelte:window onkeydown={onKey} />

<div class="wb flex h-screen flex-col bg-white text-[12px] text-cv-ink-950">
	<header class="flex h-9 shrink-0 items-center gap-4 bg-cv-ink-950 pr-2 pl-3 text-cv-mint-50">
		<div class="flex items-baseline gap-2">
			<span class="sans text-[20px] leading-none font-bold tracking-[-0.04em] text-cv-mint-300">sudo</span>
			<span class="text-[10px] text-cv-mint-50/60">&times; Certivity</span>
		</div>
		<nav class="flex h-full items-stretch text-[11px] text-cv-mint-50/80">
			<button
				type="button"
				disabled={app.loading}
				onclick={() => app.submit()}
				class="px-2.5 hover:bg-cv-ink-800 hover:text-white disabled:opacity-60"
			>
				{app.loading ? 'Running…' : 'Run'} <kbd>⌘↵</kbd>
			</button>
			<button
				type="button"
				disabled={!app.result}
				onclick={() => app.download()}
				class="px-2.5 hover:bg-cv-ink-800 hover:text-white disabled:opacity-40"
			>
				Export JSON
			</button>
			<a href="/v" class="flex items-center px-2.5 hover:bg-cv-ink-800 hover:text-white">Variants</a>
		</nav>
		<div class="ml-auto truncate text-[11px] text-cv-mint-50/60">
			{app.selectedCase || 'no case'} &mdash; requirements.json
		</div>
	</header>

	<div class="grid min-h-0 flex-1 grid-cols-[15rem_minmax(0,1fr)_minmax(0,0.7fr)] xl:grid-cols-[19rem_minmax(0,1fr)_minmax(0,1fr)]">
		<aside class="flex min-h-0 flex-col border-r border-cv-ink-950/20 bg-cv-mint-50">
			<div class="pane-head">
				<span>Input</span>
				<span class="opacity-60">{app.loading ? 'running' : 'ready'}</span>
			</div>
			<form
				class="space-y-2 border-b border-cv-ink-950/20 p-2"
				onsubmit={(e) => {
					e.preventDefault();
					app.submit();
				}}
			>
				<div class="flex items-center gap-2">
					<span class="w-10 shrink-0 text-[10px] text-cv-teal-700 uppercase">case</span>
					<Select.Root
						type="single"
						value={app.selectedCase}
						onValueChange={(v) => app.loadCase(v)}
						items={app.cases.map((c) => ({ value: c, label: c }))}
					>
						<Select.Trigger
							class="flex h-6 min-w-0 flex-1 items-center justify-between border border-cv-ink-950/30 bg-white px-1.5 text-[12px] hover:border-cv-teal-700 focus:border-cv-teal-700 focus:outline-none"
						>
							<span class="truncate">{app.selectedCase || 'select…'}</span>
							<span aria-hidden="true" class="text-[9px] opacity-60">▼</span>
						</Select.Trigger>
						<Select.Portal>
							<Select.Content
								sideOffset={1}
								class="wb z-50 max-h-64 w-(--bits-select-anchor-width) overflow-auto border border-cv-ink-950/40 bg-white text-[12px] text-cv-ink-950"
							>
								<Select.Viewport>
									{#each app.cases as c (c)}
										<Select.Item
											value={c}
											label={c}
											class="cursor-default px-1.5 py-0.5 data-highlighted:bg-cv-mint-300 data-selected:font-bold"
										>
											{c}
										</Select.Item>
									{/each}
								</Select.Viewport>
							</Select.Content>
						</Select.Portal>
					</Select.Root>
				</div>
				<div>
					<div class="mb-0.5 flex items-center justify-between text-[10px] text-cv-teal-700 uppercase">
						<span>spec.md</span>
						<label class="cursor-pointer normal-case underline">
							open file…
							<input
								type="file"
								accept=".md,.txt,text/*"
								onchange={(e) => app.setSpecFile(e.currentTarget.files?.[0])}
								class="sr-only"
							/>
						</label>
					</div>
					<textarea
						bind:value={app.spec}
						rows="10"
						spellcheck="false"
						class="block w-full resize-y border border-cv-ink-950/30 bg-white px-1.5 py-1 text-[11px] leading-[1.35] focus:border-cv-teal-700 focus:outline-none"
					></textarea>
				</div>
				<div>
					<div class="mb-0.5 flex items-center justify-between text-[10px] text-cv-teal-700 uppercase">
						<span>exploded_view.png</span>
						<label class="cursor-pointer normal-case underline">
							open file…
							<input
								type="file"
								accept="image/*"
								onchange={(e) => app.setImageFile(e.currentTarget.files?.[0])}
								class="sr-only"
							/>
						</label>
					</div>
					<div class="flex h-24 items-center justify-center border border-cv-ink-950/30 bg-white">
						{#if app.imageUrl}
							<img src={app.imageUrl} alt="Exploded view" class="max-h-full max-w-full object-contain p-1" />
						{:else}
							<span class="opacity-50">no image</span>
						{/if}
					</div>
				</div>
				<div class="flex gap-1.5">
					<button
						disabled={app.loading}
						class="h-6 flex-1 bg-cv-teal-700 font-medium text-white hover:bg-cv-ink-800 disabled:opacity-60"
					>
						{app.loading ? '● running…' : '▶ Run'}
					</button>
					<button
						type="button"
						disabled={!app.result}
						onclick={() => app.download()}
						class="h-6 border border-cv-ink-950/30 bg-white px-2 hover:border-cv-teal-700 disabled:opacity-40"
					>
						↓ JSON
					</button>
				</div>
			</form>

			<div class="pane-head">
				<span>Regulations</span>
				<span class="opacity-60">{app.byRegulation.length}</span>
			</div>
			<div class="min-h-0 flex-1 overflow-auto py-0.5">
				{#each app.byRegulation as g (g.regulation)}
					<button
						type="button"
						onclick={() => (collapsed[g.regulation] = !collapsed[g.regulation])}
						class="flex w-full items-baseline gap-1 px-1.5 py-[1px] text-left hover:bg-cv-mint-300/40"
					>
						<span class="w-3 text-[9px] opacity-60">{collapsed[g.regulation] ? '▸' : '▾'}</span>
						<span class="font-bold">{g.regulation}</span>
						<span class="sans min-w-0 flex-1 truncate opacity-70">{g.title}</span>
						<span class="text-cv-teal-700">{g.count}</span>
					</button>
					{#if !collapsed[g.regulation]}
						{#each g.requirements as req (req.id)}
							<button
								type="button"
								onclick={() => move(rows.findIndex((r) => r.id === req.id))}
								class="flex w-full gap-2 py-[1px] pr-1.5 pl-6 text-left {app.selectedId === req.id
									? 'bg-cv-mint-300 text-cv-ink-950'
									: 'hover:bg-cv-mint-300/40'}"
							>
								<span class="opacity-70">{req.id}</span>
								<span>§ {req.source.paragraph ?? '—'}</span>
								<span class="ml-auto opacity-60">p{req.source.page}</span>
							</button>
						{/each}
					{/if}
				{:else}
					<p class="px-2 py-1 opacity-50">no results</p>
				{/each}
			</div>
		</aside>

		<main class="flex min-h-0 flex-col border-r border-cv-ink-950/20">
			<div class="pane-head">
				<span>Requirements</span>
				<span class="opacity-60">{rows.length}/{total}</span>
			</div>
			<div class="flex items-center gap-2 border-b border-cv-ink-950/15 px-2 py-1">
				<span class="text-cv-teal-700">/</span>
				<input
					bind:this={filterEl}
					bind:value={filter}
					placeholder="filter by id, text, regulation, paragraph"
					class="min-w-0 flex-1 bg-transparent text-[12px] placeholder:text-cv-ink-950/40 focus:outline-none"
				/>
				{#if filter}
					<button type="button" class="opacity-60 hover:opacity-100" onclick={() => (filter = '')}>clear</button>
				{/if}
			</div>
			{#if app.error}
				<div class="border-b border-[#c62828] bg-[#c62828]/10 px-2 py-1 text-[#b71c1c]">
					error: {app.error}
				</div>
			{/if}
			<div class="grid grid-cols-[2rem_4.25rem_3.5rem_3.25rem_4.25rem_minmax(0,1fr)_2.5rem] border-b border-cv-ink-950/15 bg-cv-mint-50 text-[10px] tracking-wide text-cv-teal-700 uppercase">
				<span class="px-1.5 py-0.5 text-right">#</span>
				<span class="px-1.5 py-0.5">id</span>
				<span class="px-1.5 py-0.5">reg</span>
				<span class="px-1.5 py-0.5">ver</span>
				<span class="px-1.5 py-0.5">para</span>
				<span class="px-1.5 py-0.5">text</span>
				<span class="px-1.5 py-0.5 text-right">pg</span>
			</div>
			<div bind:this={listEl} class="min-h-0 flex-1 overflow-auto" role="listbox" aria-label="Requirements" tabindex="-1">
				{#each rows as req, i (req.id)}
					{@const url = app.pdfUrl(req.source)}
					{@const sel = app.selectedId === req.id}
					<div
						data-id={req.id}
						role="option"
						aria-selected={sel}
						tabindex="-1"
						onclick={() => app.select(req.id)}
						onkeydown={(e) => e.key === ' ' && app.select(req.id)}
						class="grid cursor-default grid-cols-[2rem_4.25rem_3.5rem_3.25rem_4.25rem_minmax(0,1fr)_2.5rem] border-b border-cv-ink-950/[0.06] {sel
							? 'bg-cv-mint-300/70 shadow-[inset_2px_0_0_var(--color-cv-teal-700)]'
							: i % 2
								? 'bg-cv-mint-50/60 hover:bg-cv-mint-300/25'
								: 'hover:bg-cv-mint-300/25'}"
					>
						<span class="px-1.5 py-[2px] text-right opacity-40">{i + 1}</span>
						<span class="px-1.5 py-[2px] font-medium">{req.id}</span>
						<span class="truncate px-1.5 py-[2px]" title={req.source.regulation}
							>{req.source.regulation.replace('UN ', '')}</span
						>
						<span class="truncate px-1.5 py-[2px] opacity-60">{req.source.version}</span>
						<span class="truncate px-1.5 py-[2px]">{req.source.paragraph ?? '—'}</span>
						<span class="sans px-1.5 py-[2px] text-[12.5px] leading-[1.35] truncate {sel ? 'xl:whitespace-normal' : ''}">{req.text}</span>
						<span class="px-1.5 py-[2px] text-right">
							{#if url}
								<a
									href={url}
									target="_blank"
									rel="noreferrer"
									onclick={(e) => e.stopPropagation()}
									class="text-cv-teal-700 underline hover:text-cv-ink-950">{req.source.page}</a
								>
							{:else}
								{req.source.page}
							{/if}
						</span>
					</div>
				{:else}
					<p class="px-2 py-2 opacity-50">
						{app.loading ? 'running…' : app.result ? 'no matches' : 'no results — run a case'}
					</p>
				{/each}
			</div>
		</main>

		<section class="flex min-h-0 flex-col bg-cv-mint-50">
			<div class="pane-head">
				<span class="truncate">
					Source{#if app.selected}
						&nbsp;&mdash; {app.selected.source.regulation} @{app.selected.source.version} · p{app.selected.source.page}{/if}
				</span>
				{#if selectedUrl}
					<a href={selectedUrl} target="_blank" rel="noreferrer" class="shrink-0 underline">open ↗ <kbd>o</kbd></a>
				{/if}
			</div>
			{#if app.selected && selectedUrl}
				<div class="border-b border-cv-ink-950/15 bg-white px-2 py-1.5">
					<div class="mb-0.5 flex gap-3 text-[10px] text-cv-teal-700 uppercase">
						<span>{app.selected.id}</span>
						<span>§ {app.selected.source.paragraph ?? '—'}</span>
						<span>{app.regulationTitle(app.selected.source.regulation)}</span>
					</div>
					<p class="sans text-[13px] leading-snug">{app.selected.text}</p>
				</div>
				{#key selectedUrl}
					<iframe src={selectedUrl} title="Source page" class="min-h-0 w-full flex-1 border-0 bg-white"></iframe>
				{/key}
			{:else}
				<p class="p-3 opacity-50">no requirement selected — press <kbd>j</kbd> to start</p>
			{/if}
		</section>
	</div>

	<footer class="flex h-6 shrink-0 items-center gap-0 bg-cv-teal-700 text-[11px] text-white">
		<span class="flex h-full items-center px-2 {app.error ? 'bg-[#c62828]' : app.loading ? 'bg-cv-ink-800' : 'bg-cv-ink-950'}">
			{app.error ? '✕ error' : app.loading ? '● running' : '✓ ready'}
		</span>
		<span class="px-2">{app.selectedCase || '—'}</span>
		<span class="border-l border-white/25 px-2">{app.byRegulation.length} reg</span>
		<span class="border-l border-white/25 px-2">{total} req</span>
		{#if filter}<span class="border-l border-white/25 px-2">{rows.length} shown</span>{/if}
		<span class="border-l border-white/25 px-2">
			{cursor >= 0 ? `${cursor + 1}/${rows.length}` : `–/${rows.length}`}
		</span>
		<span class="ml-auto flex gap-3 px-2 text-white/80">
			<span><kbd>j</kbd><kbd>k</kbd> <kbd>↑</kbd><kbd>↓</kbd> move</span>
			<span><kbd>g</kbd><kbd>G</kbd> first/last</span>
			<span><kbd>/</kbd> filter</span>
			<span><kbd>o</kbd> open page</span>
			<span><kbd>⌘↵</kbd> run</span>
		</span>
	</footer>
</div>

<style>
	:global(.wb) {
		font-family: 'JetBrains Mono', ui-monospace, monospace;
	}
	.sans {
		font-family: 'Space Grotesk', system-ui, sans-serif;
	}
	.pane-head {
		display: flex;
		flex-shrink: 0;
		align-items: center;
		justify-content: space-between;
		gap: 0.5rem;
		height: 1.5rem;
		padding: 0 0.5rem;
		border-bottom: 1px solid color-mix(in srgb, var(--color-cv-ink-950) 20%, transparent);
		background: color-mix(in srgb, var(--color-cv-ink-950) 8%, white);
		font-size: 10px;
		font-weight: 700;
		letter-spacing: 0.08em;
		text-transform: uppercase;
	}
	kbd {
		display: inline-block;
		min-width: 1.1em;
		margin: 0 1px;
		padding: 0 0.25em;
		border: 1px solid currentColor;
		border-radius: 2px;
		font: inherit;
		font-size: 0.9em;
		line-height: 1.2;
		text-align: center;
		opacity: 0.85;
	}
</style>
