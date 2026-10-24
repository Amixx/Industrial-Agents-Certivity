<script lang="ts">
	import { onMount, tick } from 'svelte';
	import { Collapsible, Select } from 'bits-ui';
	import { app } from '#lib/app.svelte.ts';

	onMount(() => app.demo());

	let inputOpen = $state(false);
	const ordered = $derived(app.byRegulation.flatMap((g) => g.requirements));
	const index = $derived(ordered.findIndex((r) => r.id === app.selectedId));
	const selectedUrl = $derived(app.selected ? app.pdfUrl(app.selected.source) : null);

	$effect(() => {
		if (ordered.length && index === -1) app.select(ordered[0].id);
	});

	async function step(delta: number) {
		if (!ordered.length) return;
		const next = Math.min(ordered.length - 1, Math.max(0, index + delta));
		app.select(ordered[next].id);
		await tick();
		const el = document.getElementById(`req-${ordered[next].id}`);
		el?.scrollIntoView({ block: 'nearest' });
		el?.querySelector('button')?.focus({ preventScroll: true });
	}

	function onKeydown(e: KeyboardEvent) {
		const t = e.target as HTMLElement;
		if (t.closest('input, textarea, select, [contenteditable], [role="listbox"]')) return;
		if (e.key === 'ArrowDown' || e.key === 'j' || e.key === 'ArrowRight') {
			e.preventDefault();
			step(1);
		} else if (e.key === 'ArrowUp' || e.key === 'k' || e.key === 'ArrowLeft') {
			e.preventDefault();
			step(-1);
		}
	}
</script>

<svelte:head>
	<title>Reader</title>
	<link rel="preconnect" href="https://fonts.googleapis.com" />
	<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous" />
	<link
		rel="stylesheet"
		href="https://fonts.googleapis.com/css2?family=Instrument+Sans:ital,wght@0,400;0,500;0,600;1,400&display=swap"
	/>
</svelte:head>

<svelte:window onkeydown={onKeydown} />

<div class="grid h-screen grid-cols-2 bg-white font-['Instrument_Sans'] text-[15px] leading-relaxed text-cv-ink-950">
	<section class="flex min-h-0 flex-col bg-cv-ink-800/10">
		<div class="flex items-baseline justify-between gap-4 px-8 py-3 text-[13px] text-cv-ink-800">
			{#if app.selected}
				<span>
					<span class="font-medium">{app.selected.source.regulation}</span>
					<span class="opacity-60">· {app.regulationTitle(app.selected.source.regulation)} · revision {app.selected.source.version}</span>
				</span>
				{#if selectedUrl}
					<a href={selectedUrl} target="_blank" rel="noreferrer" class="shrink-0 underline decoration-cv-teal-500 underline-offset-4"
						>Page {app.selected.source.page} ↗</a
					>
				{/if}
			{:else}
				<span class="opacity-60">Source document</span>
			{/if}
		</div>
		<div class="min-h-0 flex-1 px-8 pb-8">
			{#if selectedUrl}
				{#key selectedUrl}
					<iframe
						src={selectedUrl}
						title="Source page"
						class="h-full w-full border border-cv-ink-800/20 bg-white"
					></iframe>
				{/key}
			{:else}
				<div class="flex h-full items-center justify-center border border-dashed border-cv-ink-800/30 text-cv-ink-800/60">
					{app.loading ? 'Reading the regulations…' : 'The source page appears here.'}
				</div>
			{/if}
		</div>
	</section>

	<section class="flex min-h-0 flex-col bg-cv-mint-50">
		<header class="flex items-end justify-between px-12 pt-8">
			<div>
				<div class="text-[12px] tracking-wide text-cv-teal-700">Certivity presents</div>
				<h1 class="text-5xl leading-none font-semibold tracking-[-0.04em]">sudo</h1>
			</div>
			<div class="flex items-center gap-5 text-[13px]">
				<button
					type="button"
					disabled={!app.result}
					onclick={() => app.download()}
					class="underline decoration-cv-teal-500 underline-offset-4 hover:text-cv-teal-700 disabled:opacity-40"
				>
					Download JSON
				</button>
				<a href="/v" class="text-cv-ink-800/60 hover:text-cv-ink-950">All variants</a>
			</div>
		</header>

		<Collapsible.Root bind:open={inputOpen} class="mx-12 mt-6 border-y border-cv-ink-800/15">
			<Collapsible.Trigger
				class="flex w-full items-baseline justify-between py-3 text-left text-[14px] hover:text-cv-teal-700"
			>
				<span>
					<span class="font-medium">Input</span>
					<span class="text-cv-ink-800/60">· {app.selectedCase || 'no case'}{app.imageUrl ? ' · with drawing' : ''}</span>
				</span>
				<span class="text-[13px] text-cv-ink-800/60">{inputOpen ? 'Close' : 'Edit and run'}</span>
			</Collapsible.Trigger>
			<Collapsible.Content>
				<form
					class="grid grid-cols-[1fr_160px] gap-5 pb-5"
					onsubmit={(e) => {
						e.preventDefault();
						app.submit();
					}}
				>
					<div class="flex flex-col gap-3">
						<Select.Root
							type="single"
							value={app.selectedCase}
							onValueChange={(v) => app.loadCase(v)}
							items={app.cases.map((c) => ({ value: c, label: c }))}
						>
							<Select.Trigger
								class="flex h-9 w-full items-center justify-between rounded-sm border border-cv-ink-800/25 bg-white px-3 text-[14px]"
							>
								{app.selectedCase || 'Choose a case'}
								<span aria-hidden="true" class="text-cv-ink-800/50">▾</span>
							</Select.Trigger>
							<Select.Portal>
								<Select.Content
									sideOffset={4}
									class="z-50 max-h-64 w-(--bits-select-anchor-width) overflow-auto rounded-sm border border-cv-ink-800/25 bg-white py-1 font-['Instrument_Sans'] text-[14px] text-cv-ink-950"
								>
									<Select.Viewport>
										{#each app.cases as c (c)}
											<Select.Item
												value={c}
												label={c}
												class="cursor-default px-3 py-1.5 data-highlighted:bg-cv-mint-50 data-selected:text-cv-teal-700"
											>
												{c}
											</Select.Item>
										{/each}
									</Select.Viewport>
								</Select.Content>
							</Select.Portal>
						</Select.Root>
						<textarea
							bind:value={app.spec}
							rows="8"
							class="w-full resize-y rounded-sm border border-cv-ink-800/25 bg-white p-3 text-[13px] leading-relaxed"
						></textarea>
						<label class="text-[13px] text-cv-ink-800/70">
							Spec from file
							<input
								type="file"
								accept=".md,.txt,text/*"
								onchange={(e) => app.setSpecFile(e.currentTarget.files?.[0])}
								class="file-in ml-2"
							/>
						</label>
					</div>
					<div class="flex flex-col gap-3">
						<div class="flex h-32 items-center justify-center rounded-sm border border-cv-ink-800/25 bg-white p-2">
							{#if app.imageUrl}
								<img src={app.imageUrl} alt="Exploded view" class="max-h-full max-w-full object-contain" />
							{:else}
								<span class="text-[13px] text-cv-ink-800/50">No drawing</span>
							{/if}
						</div>
						<input
							type="file"
							accept="image/*"
							onchange={(e) => app.setImageFile(e.currentTarget.files?.[0])}
							class="file-in"
						/>
						<button
							disabled={app.loading}
							class="mt-auto h-10 rounded-sm bg-cv-ink-950 text-[14px] font-medium text-white hover:bg-cv-teal-700 disabled:opacity-60"
						>
							{app.loading ? 'Running…' : 'Run'}
						</button>
					</div>
				</form>
			</Collapsible.Content>
		</Collapsible.Root>

		{#if app.error}
			<p class="mx-12 mt-4 text-[14px] text-red-700">Something went wrong: {app.error}</p>
		{/if}

		<div class="max-h-[50%] shrink-0 overflow-auto border-b border-cv-ink-800/15 px-12">
			{#if app.selected}
				<div class="pt-8 pb-7">
					<div class="mb-4 flex items-baseline justify-between text-[13px] text-cv-ink-800/70">
						<span class="tabular-nums">{index + 1} of {ordered.length}</span>
						<span class="flex gap-2">
							<button type="button" onclick={() => step(-1)} disabled={index <= 0} class="navbtn">Previous</button>
							<button
								type="button"
								onclick={() => step(1)}
								disabled={index >= ordered.length - 1}
								class="navbtn">Next</button
							>
						</span>
					</div>
					<blockquote class="border-l-2 border-cv-teal-500 pl-6 text-[20px] leading-[1.45] xl:text-[24px] font-normal tracking-[-0.01em]">
						“{app.selected.text}”
					</blockquote>
					<p class="mt-5 pl-6 text-[14px] text-cv-ink-800">
						— {app.selected.source.regulation}, revision {app.selected.source.version}{#if app.selected.source.paragraph},
							paragraph {app.selected.source.paragraph}{/if},
						{#if selectedUrl}
							<a href={selectedUrl} target="_blank" rel="noreferrer" class="underline decoration-cv-teal-500 underline-offset-4"
								>page {app.selected.source.page}</a
							>
						{:else}
							page {app.selected.source.page}
						{/if}
						<span class="ml-2 text-cv-ink-800/50">{app.selected.id}</span>
					</p>
					<p class="mt-4 pl-6 text-[12px] text-cv-ink-800/50">Use ↑ ↓ or j k to step through.</p>
				</div>
			{:else if app.loading}
				<p class="py-8 text-cv-ink-800/60">Reading the regulations…</p>
			{/if}

		</div>

		<div class="min-h-0 flex-1 overflow-auto px-12 pb-12">
			{#if app.byRegulation.length}
				<p class="pt-5 text-[14px] text-cv-ink-800">
					{ordered.length} requirements from
					{#each app.byRegulation as g, i (g.regulation)}
						{i ? (i === app.byRegulation.length - 1 ? ' and ' : ', ') : ''}<span class="font-medium">{g.regulation}</span>
						<span class="text-cv-ink-800/60">{g.title} ({g.count})</span>{/each}.
				</p>
			{/if}

			{#each app.byRegulation as g (g.regulation)}
				<h2 class="mt-8 mb-2 text-[13px] font-medium text-cv-teal-700">{g.regulation} · {g.title}</h2>
				<ol>
					{#each g.requirements as req (req.id)}
						{@const url = app.pdfUrl(req.source)}
						{@const active = app.selectedId === req.id}
						<li id="req-{req.id}" class="scroll-my-4">
							<button
								type="button"
								onclick={() => app.select(req.id)}
								class="grid w-full grid-cols-[64px_1fr] gap-4 border-t border-cv-ink-800/10 py-3 text-left focus:outline-none focus-visible:shadow-[inset_0_2px_0_var(--color-cv-teal-500)] {active
									? 'text-cv-ink-950'
									: 'text-cv-ink-800/75 hover:text-cv-ink-950'}"
							>
								<span class="pt-0.5 text-[12px] tabular-nums {active ? 'font-semibold text-cv-teal-700' : 'text-cv-ink-800/50'}">
									{req.id}
								</span>
								<span class={active ? 'font-medium' : ''}>{req.text}</span>
							</button>
							<div class="-mt-1.5 grid grid-cols-[64px_1fr] gap-4 pb-3 text-[12px] text-cv-ink-800/55">
								<span></span>
								<span>
									revision {req.source.version}{#if req.source.paragraph} · ¶ {req.source.paragraph}{/if} ·
									{#if url}
										<a href={url} target="_blank" rel="noreferrer" class="underline underline-offset-2 hover:text-cv-teal-700"
											>p. {req.source.page}</a
										>
									{:else}
										p. {req.source.page}
									{/if}
								</span>
							</div>
						</li>
					{/each}
				</ol>
			{/each}
		</div>
	</section>
</div>

<style>
	.navbtn {
		border: 1px solid color-mix(in srgb, var(--color-cv-ink-800) 25%, transparent);
		background: white;
		padding: 0.15rem 0.85rem;
		border-radius: 2px;
		color: var(--color-cv-ink-950);
	}
	.navbtn:hover:not(:disabled) {
		border-color: var(--color-cv-teal-700);
		color: var(--color-cv-teal-700);
	}
	.navbtn:disabled {
		opacity: 0.35;
	}
	.file-in {
		font-size: 12px;
	}
	.file-in::file-selector-button {
		margin-right: 0.5rem;
		border: 1px solid color-mix(in srgb, var(--color-cv-ink-800) 25%, transparent);
		border-radius: 2px;
		background: white;
		padding: 0.15rem 0.6rem;
		font: inherit;
	}
</style>
