<script lang="ts">
import { Select } from 'bits-ui';
import { onMount } from 'svelte';
import { app } from '#lib/app.svelte.ts';

onMount(() => app.demo());

const selectedUrl = $derived(app.selected ? app.pdfUrl(app.selected.source) : null);
const total = $derived(app.result?.requirements.length ?? 0);
const maxCount = $derived(Math.max(1, ...app.byRegulation.map((g) => g.count)));
const pages = $derived(
	new Set(app.result?.requirements.map((r) => `${r.source.regulation}:${r.source.page}`)).size,
);
const status = $derived(
	app.loading ? 'RUNNING' : app.error ? 'FAULT' : app.result ? 'NOMINAL' : 'STANDBY',
);

const pad = (n: number, w = 3) => String(n).padStart(w, '0');
</script>

<svelte:head>
	<title>Instrument panel</title>
	<link rel="preconnect" href="https://fonts.googleapis.com">
	<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous">
	<link
		rel="stylesheet"
		href="https://fonts.googleapis.com/css2?family=B612:wght@400;700&family=B612+Mono:wght@400;700&display=swap"
	>
</svelte:head>

<div class="flex h-screen flex-col bg-cv-ink-950 font-['B612'] text-[13px] text-cv-mint-50">
	<header class="flex items-center gap-6 border-b border-cv-ink-800 px-5 py-3">
		<div class="flex items-baseline gap-3">
			<h1 class="font-['B612_Mono'] text-3xl leading-none font-bold tracking-tight text-white">
				sudo<span class="text-cv-teal-400">_</span>
			</h1>
			<span class="text-[10px] tracking-[0.25em] text-cv-mint-50/50 uppercase">w/ Certivity</span>
		</div>
		<div
			class="ml-4 flex items-center gap-2 border-l border-cv-ink-800 pl-6 text-[11px] tracking-[0.18em]"
		>
			<span
				class="size-2 {app.loading
					? 'animate-pulse bg-cv-mint-300'
					: app.error
						? 'bg-red-500'
						: app.result
							? 'bg-cv-teal-400'
							: 'bg-cv-mint-50/30'}"
			></span>
			<span class={app.error ? 'text-red-400' : 'text-cv-mint-50/80'}>SYS {status}</span>
		</div>
		<span class="font-['B612_Mono'] text-[11px] text-cv-mint-50/50"
			>CASE {app.result?.case_id ?? '—'}</span
		>
		<a
			href="/v"
			class="ml-auto text-[11px] tracking-[0.18em] text-cv-mint-50/60 uppercase hover:text-cv-mint-300"
			>All variants</a
		>
	</header>

	<section
		class="grid grid-cols-[repeat(3,minmax(0,160px))_minmax(0,200px)_1fr] border-b border-cv-ink-800"
	>
		{#each [
			{ k: 'Requirements', v: pad(total) },
			{ k: 'Regulations', v: pad(app.byRegulation.length, 2) },
			{ k: 'Pages cited', v: pad(pages, 2) },
			{ k: 'Selected', v: app.selected?.id ?? '----' },
		] as r (r.k)}
			<div class="border-r border-cv-ink-800 px-5 py-4">
				<div class="text-[10px] tracking-[0.22em] text-cv-mint-50/50 uppercase">{r.k}</div>
				<div
					class="mt-1 font-['B612_Mono'] leading-none whitespace-nowrap text-white tabular-nums {r.k ===
					'Selected'
						? 'pt-2 text-[32px]'
						: 'text-[44px]'}"
				>
					{app.loading && r.k !== 'Selected' ? '···' : r.v}
				</div>
			</div>
		{/each}
		<div class="flex flex-col justify-center gap-2 px-5 py-3">
			{#each app.byRegulation as g (g.regulation)}
				<div class="grid grid-cols-[80px_1fr_36px] items-center gap-3">
					<span class="font-['B612_Mono'] text-[11px] text-cv-mint-50/80" title={g.title}
						>{g.regulation}</span
					>
					<div class="flex h-3 gap-[3px]">
						{#each Array.from({ length: maxCount }, (_, i) => g.requirements[i]) as req, i (i)}
							{#if req}
								<button
									type="button"
									title="{req.id} · p.{req.source.page}"
									aria-label="Select {req.id}"
									onclick={() => app.select(req.id)}
									class="flex-1 cursor-pointer {app.selectedId === req.id
										? 'bg-cv-mint-300 outline outline-1 outline-offset-2 outline-cv-mint-300'
										: 'bg-cv-teal-700 hover:bg-cv-teal-400'}"
								></button>
							{:else}
								<span class="flex-1 border border-cv-ink-800"></span>
							{/if}
						{/each}
					</div>
					<span class="text-right font-['B612_Mono'] text-[13px] text-cv-mint-300 tabular-nums"
						>{pad(g.count, 2)}</span
					>
				</div>
			{:else}
				<span class="text-[11px] tracking-[0.18em] text-cv-mint-50/40">NO DATA</span>
			{/each}
		</div>
	</section>

	{#if app.error}
		<p
			class="border-b border-red-500/60 bg-red-500/10 px-5 py-1.5 font-['B612_Mono'] text-xs text-red-300"
		>
			FAULT · {app.error}
		</p>
	{/if}

	<div
		class="grid min-h-0 flex-1 grid-cols-[220px_minmax(0,1fr)_minmax(300px,32%)] xl:grid-cols-[260px_minmax(0,1fr)_minmax(340px,36%)]"
	>
		<form
			class="flex min-h-0 flex-col gap-4 overflow-auto border-r border-cv-ink-800 p-4"
			onsubmit={(e) => {
				e.preventDefault();
				app.submit();
			}}
		>
			<div>
				<div class="lbl">Input · case</div>
				<Select.Root
					type="single"
					value={app.selectedCase}
					onValueChange={(v) => app.loadCase(v)}
					items={app.cases.map((c) => ({ value: c, label: c }))}
				>
					<Select.Trigger
						class="flex h-8 w-full items-center justify-between border border-cv-ink-800 bg-black/20 px-2 font-['B612_Mono'] text-xs text-white hover:border-cv-teal-700"
					>
						{app.selectedCase || 'SELECT'}
						<span aria-hidden="true" class="text-cv-teal-400">▾</span>
					</Select.Trigger>
					<Select.Portal>
						<Select.Content
							sideOffset={2}
							class="z-50 max-h-64 w-(--bits-select-anchor-width) overflow-auto border border-cv-teal-700 bg-cv-ink-950 font-['B612_Mono'] text-xs text-cv-mint-50"
						>
							<Select.Viewport>
								{#each app.cases as c (c)}
									<Select.Item
										value={c}
										label={c}
										class="cursor-default px-2 py-1.5 data-highlighted:bg-cv-ink-800 data-selected:text-cv-mint-300"
									>
										{c}
									</Select.Item>
								{/each}
							</Select.Viewport>
						</Select.Content>
					</Select.Portal>
				</Select.Root>
			</div>

			<label class="flex min-h-40 flex-1 flex-col">
				<span class="lbl">Spec</span>
				<textarea
					bind:value={app.spec}
					class="min-h-0 flex-1 resize-none border border-cv-ink-800 bg-black/20 p-2 font-['B612_Mono'] text-[11px] leading-snug text-cv-mint-50/90 focus:border-cv-teal-700 focus:outline-none"
				></textarea>
				<input
					type="file"
					accept=".md,.txt,text/*"
					onchange={(e) => app.setSpecFile(e.currentTarget.files?.[0])}
					class="file-in mt-1.5"
				>
			</label>

			<div>
				<span class="lbl">Exploded view</span>
				<div class="flex h-28 items-center justify-center border border-cv-ink-800 bg-white">
					{#if app.imageUrl}
						<img
							src={app.imageUrl}
							alt="Exploded view"
							class="max-h-full max-w-full object-contain p-1"
						>
					{:else}
						<span class="text-[11px] text-cv-ink-800/60">NO IMAGE</span>
					{/if}
				</div>
				<input
					type="file"
					accept="image/*"
					onchange={(e) => app.setImageFile(e.currentTarget.files?.[0])}
					class="file-in mt-1.5"
				>
			</div>

			<div class="grid grid-cols-2 gap-2">
				<button
					type="submit"
					disabled={app.loading}
					class="h-9 bg-cv-teal-500 text-xs font-bold tracking-[0.2em] text-cv-ink-950 uppercase hover:bg-cv-mint-300 disabled:bg-cv-ink-800 disabled:text-cv-mint-50/60"
				>
					{app.loading ? 'Running' : 'Run'}
				</button>
				<button
					type="button"
					disabled={!app.result}
					onclick={() => app.download()}
					class="h-9 border border-cv-teal-700 text-xs tracking-[0.2em] text-cv-mint-50 uppercase hover:border-cv-mint-300 disabled:opacity-40"
				>
					JSON ↓
				</button>
			</div>
		</form>

		<main class="min-h-0 overflow-auto">
			<table class="w-full border-collapse text-left">
				<thead class="sticky top-0 z-10 bg-cv-ink-950">
					<tr
						class="border-b border-cv-ink-800 text-[10px] tracking-[0.2em] text-cv-mint-50/50 uppercase"
					>
						<th class="hidden w-12 py-2 pl-4 font-normal xl:table-cell">#</th>
						<th class="w-20 py-2 pl-4 font-normal xl:pl-0">ID</th>
						<th class="hidden w-14 py-2 font-normal xl:table-cell">Reg</th>
						<th class="py-2 pr-3 font-normal">Requirement</th>
						<th class="hidden w-14 py-2 font-normal xl:table-cell">Rev</th>
						<th class="hidden w-16 py-2 font-normal xl:table-cell">Para</th>
						<th class="w-14 py-2 pr-4 text-right font-normal">Pg</th>
					</tr>
				</thead>
				<tbody class="font-['B612_Mono'] text-[12px]">
					{#each app.byRegulation.flatMap((g) => g.requirements) as req, i (req.id)}
						{@const url = app.pdfUrl(req.source)}
						{@const active = app.selectedId === req.id}
						<tr
							onclick={() => app.select(req.id)}
							class="cursor-pointer border-b border-cv-ink-800/60 align-top {active
								? 'bg-cv-ink-800 text-white'
								: 'text-cv-mint-50/80 hover:bg-cv-ink-800/40'}"
						>
							<td
								class="hidden py-2 pl-4 xl:table-cell {active
									? 'text-cv-mint-300 shadow-[inset_2px_0_0_var(--color-cv-mint-300)]'
									: 'text-cv-mint-50/40'}"
							>
								{pad(i + 1)}
							</td>
							<td class="py-2 pl-4 whitespace-nowrap text-cv-teal-400 xl:pl-0">{req.id}</td>
							<td class="hidden py-2 whitespace-nowrap xl:table-cell">
								{req.source.regulation.replace('UN ', '')}
							</td>
							<td class="py-2 pr-3 font-['B612'] text-[12.5px] leading-snug">
								{req.text}
								<span class="mt-1 block text-[11px] text-cv-mint-50/50 tabular-nums xl:hidden">
									{req.source.regulation}
									· r{req.source.version}
									· §{req.source.paragraph ?? '—'}
								</span>
							</td>
							<td class="hidden py-2 font-['B612'] whitespace-nowrap tabular-nums xl:table-cell">
								{req.source.version}
							</td>
							<td class="hidden py-2 font-['B612'] whitespace-nowrap tabular-nums xl:table-cell">
								{req.source.paragraph ?? '—'}
							</td>
							<td class="py-2 pr-4 text-right">
								{#if url}
									<a
										href={url}
										target="_blank"
										rel="noreferrer"
										onclick={(e) => e.stopPropagation()}
										class="text-cv-mint-300 underline decoration-cv-teal-700 underline-offset-2 hover:decoration-cv-mint-300"
										>{pad(req.source.page)}</a
									>
								{:else}
									{pad(req.source.page)}
								{/if}
							</td>
						</tr>
					{:else}
						<tr>
							<td colspan="7" class="px-4 py-6 text-[11px] tracking-[0.2em] text-cv-mint-50/40">
								{app.loading ? 'ACQUIRING…' : 'NO READOUT'}
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</main>

		<aside class="flex min-h-0 flex-col border-l border-cv-ink-800 p-4">
			<div class="mb-2 flex items-baseline justify-between font-['B612_Mono'] text-[11px]">
				<span class="tracking-[0.2em] text-cv-mint-50/50">SOURCE</span>
				{#if app.selected}
					<span class="font-['B612'] text-cv-mint-300 tabular-nums">
						{app.selected.source.regulation}
						r{app.selected.source.version}
						· §{app.selected.source.paragraph ?? '—'}
						· P{pad(app.selected.source.page)}
					</span>
				{/if}
			</div>
			<div
				class="screen relative min-h-0 flex-1 border border-cv-teal-700/70 bg-cv-ink-800/40 p-1.5"
			>
				{#if app.selected && selectedUrl}
					{#key selectedUrl}
						<iframe
							src={selectedUrl}
							title="Source page"
							class="h-full w-full border-0 bg-white"
						></iframe>
					{/key}
				{:else}
					<div
						class="flex h-full items-center justify-center text-[11px] tracking-[0.3em] text-cv-mint-50/30"
					>
						NO SIGNAL · SELECT A ROW
					</div>
				{/if}
			</div>
			{#if app.selected}
				<p
					class="mt-3 border-l-2 border-cv-teal-500 pl-3 text-[12px] leading-snug text-cv-mint-50/80"
				>
					{app.selected.text}
				</p>
			{/if}
		</aside>
	</div>
</div>

<style>
.lbl {
	display: block;
	margin-bottom: 0.35rem;
	font-size: 10px;
	letter-spacing: 0.22em;
	text-transform: uppercase;
	color: color-mix(in srgb, var(--color-cv-mint-50) 50%, transparent);
}
.file-in {
	display: block;
	width: 100%;
	font-family: "B612 Mono", monospace;
	font-size: 10px;
	color: color-mix(in srgb, var(--color-cv-mint-50) 60%, transparent);
}
.file-in::file-selector-button {
	margin-right: 0.5rem;
	border: 1px solid var(--color-cv-ink-800);
	background: transparent;
	color: var(--color-cv-mint-50);
	padding: 0.2rem 0.5rem;
	font: inherit;
	cursor: pointer;
}
.screen::before,
.screen::after {
	content: "";
	position: absolute;
	width: 14px;
	height: 14px;
	border-color: var(--color-cv-mint-300);
	pointer-events: none;
}
.screen::before {
	top: -4px;
	left: -4px;
	border-top: 2px solid;
	border-left: 2px solid;
}
.screen::after {
	right: -4px;
	bottom: -4px;
	border-right: 2px solid;
	border-bottom: 2px solid;
}
</style>
