<script lang="ts">
import { Select } from 'bits-ui';
import { onMount, tick } from 'svelte';
import { app } from '#lib/app.svelte.ts';

onMount(() => app.demo());

let filter = $state<string | null>(null);
const total = $derived(app.result?.requirements.length ?? 0);
const visible = $derived(
	(app.result?.requirements ?? []).filter((r) => !filter || r.source.regulation === filter),
);
const selectedUrl = $derived(app.selected ? app.pdfUrl(app.selected.source) : null);
const status = $derived(
	app.loading ? 'RUNNING' : app.error ? 'ERROR' : app.result ? `OK · ${total} REQ` : 'IDLE',
);

async function step(delta: number) {
	if (!visible.length) return;
	const i = visible.findIndex((r) => r.id === app.selectedId);
	const next = visible[Math.min(visible.length - 1, Math.max(0, i + delta))];
	app.select(next.id);
	await tick();
	document.querySelector(`[data-req="${next.id}"]`)?.scrollIntoView({ block: 'nearest' });
}

function onkeydown(e: KeyboardEvent) {
	const t = e.target as HTMLElement;
	if (t.closest('input, textarea, [role=listbox], [role=combobox]')) return;
	if (e.key === 'ArrowDown' || e.key === 'j') step(1);
	else if (e.key === 'ArrowUp' || e.key === 'k') step(-1);
	else if (e.key === 'Escape') app.select(null);
	else return;
	e.preventDefault();
}
</script>

<svelte:window {onkeydown} />

<svelte:head>
	<title>sudo — Utility</title>
</svelte:head>

<div class="ut-root flex h-screen flex-col bg-white text-black">
	<header class="flex shrink-0 items-stretch border-b-2 border-black">
		<h1
			class="flex items-center border-r-2 border-black px-4 text-5xl leading-none font-black tracking-tighter"
		>
			sudo
		</h1>
		<div class="flex flex-col justify-center border-r-2 border-black px-4">
			<span class="lbl">Requirements finder</span>
			<span class="text-sm font-bold">UN Regulations → cited source pages</span>
		</div>
		<div class="flex flex-col justify-center px-4">
			<span class="lbl">Case</span>
			<span class="ut-mono text-sm font-bold">{app.result?.case_id ?? '—'}</span>
		</div>
		<div class="ml-auto flex items-stretch">
			<span class="lbl flex items-center border-l-2 border-black px-4">Built with Certivity</span>
			<a
				href="/v"
				class="lbl flex items-center border-l-2 border-black px-4 hover:bg-black hover:text-white"
			>
				All variants
			</a>
		</div>
	</header>

	<form
		class="grid shrink-0 grid-cols-[15rem_minmax(0,1fr)_13rem_11rem] border-b-2 border-black xl:grid-cols-[17rem_minmax(0,1fr)_16rem_13rem]"
		onsubmit={(e) => {
			e.preventDefault();
			app.submit();
		}}
	>
		<div class="flex flex-col gap-2 border-r-2 border-black p-3">
			<div>
				<span class="lbl block">Case</span>
				<Select.Root
					type="single"
					value={app.selectedCase}
					onValueChange={(v) => app.loadCase(v)}
					items={app.cases.map((c) => ({ value: c, label: c }))}
				>
					<Select.Trigger
						class="ut-mono flex h-8 w-full items-center justify-between border-2 border-black px-2 text-left text-sm font-bold data-[state=open]:bg-cv-mint-300"
					>
						{app.selectedCase || 'SELECT'}
						<span aria-hidden="true">▼</span>
					</Select.Trigger>
					<Select.Portal>
						<Select.Content
							sideOffset={-2}
							class="ut-mono z-50 max-h-64 w-(--bits-select-anchor-width) overflow-auto border-2 border-black bg-white text-sm"
						>
							<Select.Viewport>
								{#each app.cases as c (c)}
									<Select.Item
										value={c}
										label={c}
										class="cursor-default border-b border-black px-2 py-1.5 last:border-b-0 data-highlighted:bg-black data-highlighted:text-white data-selected:font-bold"
									>
										{c}
									</Select.Item>
								{/each}
							</Select.Viewport>
						</Select.Content>
					</Select.Portal>
				</Select.Root>
			</div>
			<label class="block">
				<span class="lbl block">Spec file</span>
				<input
					type="file"
					accept=".md,.txt,text/*"
					onchange={(e) => app.setSpecFile(e.currentTarget.files?.[0])}
					class="file"
				>
			</label>
			<label class="block">
				<span class="lbl block">Drawing file</span>
				<input
					type="file"
					accept="image/*"
					onchange={(e) => app.setImageFile(e.currentTarget.files?.[0])}
					class="file"
				>
			</label>
		</div>

		<label class="flex flex-col border-r-2 border-black p-3">
			<span class="lbl"
				>Product spec <span class="ut-mono font-normal">({app.spec.length} chars)</span></span
			>
			<textarea
				bind:value={app.spec}
				rows="6"
				class="ut-mono min-h-0 flex-1 resize-none border-2 border-black p-2 text-xs leading-snug outline-none focus:bg-cv-mint-50"
			></textarea>
		</label>

		<div class="flex flex-col border-r-2 border-black p-3">
			<span class="lbl">Drawing preview</span>
			<div class="flex min-h-0 flex-1 items-center justify-center border-2 border-black">
				{#if app.imageUrl}
					<img
						src={app.imageUrl}
						alt="Exploded view"
						class="max-h-32 max-w-full object-contain p-1"
					>
				{:else}
					<span class="lbl">No image</span>
				{/if}
			</div>
		</div>

		<div class="flex flex-col">
			<button
				disabled={app.loading}
				class="flex-1 border-b-2 border-black bg-black text-xl font-black tracking-wide text-white uppercase hover:bg-cv-ink-950 disabled:cursor-wait"
			>
				{#if app.loading}
					<span class="bg-cv-mint-300 px-1 text-black">Running…</span>
				{:else}
					Run ▶
				{/if}
			</button>
			<button
				type="button"
				disabled={!app.result}
				onclick={() => app.download()}
				class="lbl h-10 border-b-2 border-black hover:bg-cv-mint-300 disabled:opacity-30"
			>
				Download JSON ↓
			</button>
			<div class="flex h-8 items-center justify-between px-3">
				<span class="lbl">Status</span>
				<span class="ut-mono text-xs font-bold {app.error ? 'text-red-600' : ''}">{status}</span>
			</div>
		</div>
	</form>

	{#if app.error}
		<p
			class="ut-mono shrink-0 border-b-2 border-black bg-red-600 px-3 py-1.5 text-sm font-bold text-white"
		>
			ERROR: {app.error}
		</p>
	{/if}

	<nav
		class="flex h-14 shrink-0 items-stretch border-b-2 border-black"
		aria-label="Regulations cited"
	>
		<button
			type="button"
			onclick={() => (filter = null)}
			class="flex w-40 shrink-0 flex-col justify-center border-r-2 border-black px-3 text-left {filter ===
			null
				? 'bg-black text-white'
				: 'hover:bg-cv-mint-50'}"
		>
			<span class="lbl">All regulations</span>
			<span class="text-2xl leading-none font-black">
				<mark class="hl">{total}</mark>
			</span>
		</button>
		{#each app.byRegulation as g (g.regulation)}
			<button
				type="button"
				onclick={() => (filter = filter === g.regulation ? null : g.regulation)}
				style:flex-grow={g.count}
				class="flex min-w-36 basis-0 items-center gap-3 overflow-hidden border-r-2 border-black px-3 text-left last:border-r-0 {filter ===
				g.regulation
					? 'bg-black text-white'
					: 'hover:bg-cv-mint-50'}"
			>
				<span class="text-2xl leading-none font-black"><mark class="hl">{g.count}</mark></span>
				<span class="min-w-0">
					<span class="block text-sm font-black uppercase">{g.regulation}</span>
					<span class="block truncate text-xs">{g.title}</span>
				</span>
			</button>
		{:else}
			<span class="lbl flex items-center px-3">{app.loading ? 'Running…' : 'No results'}</span>
		{/each}
	</nav>

	<div class="grid min-h-0 flex-1 grid-cols-[minmax(0,11fr)_minmax(0,9fr)]">
		<main class="min-h-0 overflow-auto">
			<table class="w-full border-collapse text-left text-sm">
				<thead class="sticky top-0 z-10 bg-white">
					<tr class="border-b-2 border-black">
						<th class="lbl w-6 py-1.5 pl-3"></th>
						<th class="lbl w-20 py-1.5 pr-3">ID</th>
						<th class="lbl w-24 py-1.5 pr-3">Reg / ver</th>
						<th class="lbl w-20 py-1.5 pr-3">Para</th>
						<th class="lbl w-12 py-1.5 pr-3">Page</th>
						<th class="lbl py-1.5 pr-3">
							Requirement <span class="ut-mono font-normal normal-case">[↑↓ / j k]</span>
						</th>
					</tr>
				</thead>
				<tbody>
					{#each visible as req, i (req.id)}
						{@const url = app.pdfUrl(req.source)}
						{@const active = app.selectedId === req.id}
						<tr
							data-req={req.id}
							onclick={() => app.select(req.id)}
							class="cursor-pointer border-b border-black align-top hover:bg-cv-mint-50 {active
								? 'outline-2 -outline-offset-2 outline-black'
								: ''}"
						>
							<td class="ut-mono py-2 pl-3 text-xs font-bold">{active ? '▶' : ''}</td>
							<td class="ut-mono py-2 pr-3 text-xs font-bold whitespace-nowrap">{req.id}</td>
							<td class="ut-mono py-2 pr-3 text-xs whitespace-nowrap">
								{req.source.regulation}<br><span class="opacity-70">{req.source.version}</span>
							</td>
							<td class="ut-mono py-2 pr-3 text-xs whitespace-nowrap">
								{req.source.paragraph ?? '—'}
							</td>
							<td class="ut-mono py-2 pr-3 text-xs">
								{#if url}
									<a
										href={url}
										target="_blank"
										rel="noreferrer"
										onclick={(e) => e.stopPropagation()}
										class="font-bold underline decoration-2 underline-offset-2 hover:bg-cv-mint-300"
										>{req.source.page}</a
									>
								{:else}
									{req.source.page}
								{/if}
							</td>
							<td class="py-2 pr-3 leading-snug">
								{#if active}
									<mark class="hl">{req.text}</mark>
								{:else}
									{req.text}
								{/if}
								<span class="sr-only">row {i + 1}</span>
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</main>

		<aside class="flex min-h-0 flex-col border-l-2 border-black">
			<div class="flex h-10 shrink-0 items-stretch border-b-2 border-black">
				<span class="lbl flex items-center border-r-2 border-black px-3">Source</span>
				{#if app.selected}
					<span class="ut-mono flex min-w-0 flex-1 items-center gap-3 truncate px-3 text-xs">
						<b>{app.selected.id}</b>
						<span>{app.selected.source.regulation} {app.selected.source.version}</span>
						<span>§{app.selected.source.paragraph ?? '—'}</span>
						<span>PAGE <mark class="hl font-bold">{app.selected.source.page}</mark></span>
					</span>
					{#if selectedUrl}
						<a
							href={selectedUrl}
							target="_blank"
							rel="noreferrer"
							class="lbl flex items-center border-l-2 border-black px-3 hover:bg-cv-mint-300"
							>Open ↗</a
						>
					{/if}
				{:else}
					<span class="lbl flex items-center px-3 opacity-60">No selection</span>
				{/if}
			</div>
			{#if app.selected && selectedUrl}
				{#key selectedUrl}
					<iframe src={selectedUrl} title="Source page" class="min-h-0 flex-1 border-0"></iframe>
				{/key}
			{:else}
				<div class="flex flex-1 items-start p-3">
					<p class="text-sm font-bold">Click a row, or press ↓, to load its source page here.</p>
				</div>
			{/if}
		</aside>
	</div>
</div>

<style>
:global(.ut-root) {
	font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}
:global(.ut-mono) {
	font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}
.lbl {
	font-size: 0.6875rem;
	font-weight: 800;
	letter-spacing: 0.06em;
	text-transform: uppercase;
}
.hl {
	background: var(--color-cv-mint-300);
	color: black;
	padding: 0 0.15em;
	box-decoration-break: clone;
	-webkit-box-decoration-break: clone;
}
.file {
	display: block;
	width: 100%;
	font-size: 0.75rem;
}
.file::file-selector-button {
	margin-right: 0.5rem;
	border: 2px solid black;
	background: white;
	padding: 0.125rem 0.5rem;
	font: inherit;
	font-weight: 800;
	text-transform: uppercase;
}
.file::file-selector-button:hover {
	background: var(--color-cv-mint-300);
}
</style>
