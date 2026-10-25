<script lang="ts">
import { Dialog, Select, Tabs } from 'bits-ui';
import { onMount } from 'svelte';
import { app } from '#lib/app.svelte.ts';

onMount(() => app.demo());

let drawer = $state('');
const openDrawer = $derived(
	app.byRegulation.some((g) => g.regulation === drawer)
		? drawer
		: (app.byRegulation[0]?.regulation ?? ''),
);
const selectedUrl = $derived(app.selected ? app.pdfUrl(app.selected.source) : null);
const total = $derived(app.result?.requirements.length ?? 0);
</script>

<svelte:head>
	<title>sudo — Card cc-root</title>
	<link rel="preconnect" href="https://fonts.googleapis.com">
	<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous">
	<link
		rel="stylesheet"
		href="https://fonts.googleapis.com/css2?family=Courier+Prime:wght@400;700&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;0,8..60,700;1,8..60,400&display=swap"
	>
</svelte:head>

<div class="cc-root flex h-screen flex-col bg-cv-mint-50 text-cv-ink-950">
	<header
		class="flex items-end justify-between border-b-4 border-double border-cv-ink-800 px-8 pt-5 pb-3"
	>
		<div class="flex items-end gap-6">
			<div class="plate px-6 pt-1 pb-2">
				<span class="screw left-1.5"></span>
				<span class="screw right-1.5"></span>
				<h1 class="text-5xl leading-none font-bold tracking-tight italic">sudo</h1>
			</div>
			<div class="pb-1">
				<p class="cc-typed text-xs tracking-wide">Catalogue of requirements · UN Regulations</p>
				<p class="mt-0.5 text-sm italic opacity-80">compiled in collaboration with Certivity</p>
			</div>
		</div>
		<div class="flex items-end gap-6 pb-1 text-sm">
			{#if app.result}
				<span class="cc-typed text-xs">Accession {app.result.case_id} · {total} cards</span>
			{/if}
			<a href="/v" class="underline decoration-cv-teal-700 underline-offset-4">All variants</a>
		</div>
	</header>

	<div class="grid min-h-0 flex-1 grid-cols-[22rem_1fr] xl:grid-cols-[24rem_1fr]">
		<form
			class="flex min-h-0 flex-col overflow-auto border-r border-cv-ink-800/40 p-6"
			onsubmit={(e) => {
				e.preventDefault();
				app.submit();
			}}
		>
			<div class="slip relative flex flex-1 flex-col bg-white px-5 pt-4 pb-5">
				<div class="flex items-baseline justify-between border-b-2 border-cv-teal-500 pb-1">
					<span class="cc-typed text-sm font-bold tracking-wider">REQUEST SLIP</span>
					<span class="cc-typed text-[11px] opacity-70">No. {app.result?.team_id ?? '—'}</span>
				</div>

				<div class="mt-3 grid grid-cols-[5.5rem_1fr] items-center gap-y-2 text-sm">
					<span class="cc-typed text-xs">Case</span>
					<Select.Root
						type="single"
						value={app.selectedCase}
						onValueChange={(v) => app.loadCase(v)}
						items={app.cases.map((c) => ({ value: c, label: c }))}
					>
						<Select.Trigger
							class="cc-typed flex h-8 w-full items-center justify-between border-b border-dotted border-cv-ink-800 text-left text-sm"
						>
							{app.selectedCase || 'select a case'}
							<span aria-hidden="true" class="text-xs">▾</span>
						</Select.Trigger>
						<Select.Portal>
							<Select.Content
								sideOffset={4}
								class="cc-root z-50 max-h-64 w-(--bits-select-anchor-width) overflow-auto border border-cv-ink-800 bg-white text-sm"
							>
								<Select.Viewport class="py-1">
									{#each app.cases as c (c)}
										<Select.Item
											value={c}
											label={c}
											class="cc-typed cursor-default px-3 py-1.5 data-highlighted:bg-cv-mint-50 data-selected:font-bold"
										>
											{c}
										</Select.Item>
									{/each}
								</Select.Viewport>
							</Select.Content>
						</Select.Portal>
					</Select.Root>

					<span class="cc-typed text-xs">Spec file</span>
					<input
						type="file"
						accept=".md,.txt,text/*"
						onchange={(e) => app.setSpecFile(e.currentTarget.files?.[0])}
						class="file"
					>
					<span class="cc-typed text-xs">Drawing</span>
					<input
						type="file"
						accept="image/*"
						onchange={(e) => app.setImageFile(e.currentTarget.files?.[0])}
						class="file"
					>
				</div>

				<label class="mt-4 flex min-h-40 flex-1 flex-col">
					<span class="cc-typed text-xs">Product specification</span>
					<textarea
						bind:value={app.spec}
						class="ruled mt-1 min-h-0 flex-1 resize-none bg-transparent px-1 text-[13px] leading-6 outline-none"
					></textarea>
				</label>

				<div class="mt-4">
					<span class="cc-typed text-xs">Exploded view, attached</span>
					<div
						class="mt-1 flex h-32 items-center justify-center border border-dashed border-cv-ink-800/50 bg-cv-mint-50/50 p-2"
					>
						{#if app.imageUrl}
							<img
								src={app.imageUrl}
								alt="Exploded view"
								class="max-h-full max-w-full object-contain"
							>
						{:else}
							<span class="text-sm italic opacity-60">nothing attached</span>
						{/if}
					</div>
				</div>
			</div>

			<div class="mt-4 grid grid-cols-2 gap-3">
				<button
					type="submit"
					disabled={app.loading}
					class="cc-typed h-11 border-2 border-cv-ink-950 bg-cv-ink-950 text-sm font-bold tracking-wider text-white hover:bg-cv-ink-800 disabled:cursor-wait disabled:bg-cv-ink-800"
				>
					{app.loading ? 'FILING…' : 'FILE REQUEST'}
				</button>
				<button
					type="button"
					disabled={!app.result}
					onclick={() => app.download()}
					class="cc-typed h-11 border-2 border-cv-ink-950 text-sm font-bold tracking-wider hover:bg-white disabled:opacity-40"
				>
					JSON EXPORT
				</button>
			</div>
			{#if app.error}
				<p class="cc-typed mt-3 border-l-4 border-red-700 bg-white px-3 py-2 text-xs text-red-700">
					NOT FILED — {app.error}
				</p>
			{/if}
		</form>

		<main class="flex min-h-0 flex-col">
			{#if app.byRegulation.length}
				<Tabs.Root
					value={openDrawer}
					onValueChange={(v) => (drawer = v)}
					class="flex min-h-0 flex-1 flex-col"
				>
					<Tabs.List
						class="cc-cabinet grid shrink-0 grid-cols-[repeat(auto-fill,minmax(15rem,1fr))] gap-3 px-6 pt-5 pb-0"
					>
						{#each app.byRegulation as g (g.regulation)}
							<Tabs.Trigger
								value={g.regulation}
								class="cc-drawer group relative flex flex-col items-center border-2 border-b-0 border-cv-ink-800 bg-white px-4 pt-3 pb-3 text-left data-[state=active]:bg-cv-mint-50"
							>
								<span class="holder w-full max-w-64 px-3 py-1.5 text-center">
									<span class="cc-typed block text-sm font-bold">{g.regulation}</span>
									<span class="block truncate text-xs italic">{g.title}</span>
								</span>
								<span class="mt-2 flex items-center gap-3">
									<span class="pull"></span>
									<span class="cc-typed text-xs">{g.count} {g.count === 1 ? 'card' : 'cards'}</span>
								</span>
							</Tabs.Trigger>
						{/each}
					</Tabs.List>

					{#each app.byRegulation as g (g.regulation)}
						<Tabs.Content
							value={g.regulation}
							class="min-h-0 flex-1 overflow-auto border-t-2 border-cv-ink-800 bg-cv-mint-50 px-6 py-6 outline-none"
						>
							<div class="mb-4 flex items-baseline justify-between">
								<h2 class="text-xl font-semibold">
									<span class="cc-typed">{g.regulation}</span>
									<span class="italic">— {g.title}</span>
								</h2>
								<span class="text-sm italic opacity-80">Click a card to pull its source page.</span>
							</div>
							<ul class="grid grid-cols-2 gap-5 2xl:grid-cols-3">
								{#each g.requirements as req (req.id)}
									{@const url = app.pdfUrl(req.source)}
									<li>
										<div
											role="button"
											tabindex="0"
											onclick={() => app.select(req.id)}
											onkeydown={(e) => (e.key === 'Enter' || e.key === ' ') && app.select(req.id)}
											class="card relative flex h-full cursor-pointer flex-col bg-white px-5 pt-3 pb-9 outline-none hover:-translate-y-0.5 focus-visible:ring-2 focus-visible:ring-cv-teal-500 {app.selectedId ===
											req.id
												? 'ring-2 ring-cv-ink-950'
												: ''}"
										>
											<div
												class="cc-typed flex items-baseline justify-between border-b-2 border-cv-teal-500 pb-1 text-xs"
											>
												<span class="font-bold">{req.source.regulation}· {req.source.version}</span>
												<span>§ {req.source.paragraph ?? '—'}</span>
											</div>
											<p class="card-body mt-1 flex-1 text-[15px]">{req.text}</p>
											<div class="cc-typed mt-2 flex items-baseline justify-between text-xs">
												<span>{req.id}</span>
												{#if url}
													<a
														href={url}
														target="_blank"
														rel="noreferrer"
														onclick={(e) => e.stopPropagation()}
														class="underline decoration-cv-teal-700 underline-offset-2 hover:text-cv-teal-700"
														>p. {req.source.page} ↗</a
													>
												{:else}
													<span>p. {req.source.page}</span>
												{/if}
											</div>
											<span class="cc-hole"></span>
										</div>
									</li>
								{/each}
							</ul>
						</Tabs.Content>
					{/each}
				</Tabs.Root>
			{:else}
				<div class="flex flex-1 items-center justify-center">
					<p class="cc-typed text-sm">
						{app.loading ? 'Searching the drawers…' : 'The drawers are empty.'}
					</p>
				</div>
			{/if}
		</main>
	</div>
</div>

<Dialog.Root open={app.selectedId !== null} onOpenChange={(o) => !o && app.select(null)}>
	<Dialog.Portal>
		<Dialog.Overlay class="fixed inset-0 z-40 bg-cv-ink-950/50" />
		<Dialog.Content
			class="cc-root cc-pulled fixed top-1/2 left-1/2 z-50 flex h-[88vh] w-[min(64rem,92vw)] -translate-x-1/2 -translate-y-1/2 flex-col bg-white text-cv-ink-950 outline-none"
		>
			{#if app.selected}
				<div class="flex items-start justify-between gap-6 px-7 pt-5">
					<div class="min-w-0">
						<Dialog.Title class="cc-typed text-sm font-bold">
							{app.selected.source.regulation}
							· {app.selected.source.version} · § {app.selected.source.paragraph ?? '—'} · p.
							{app.selected.source.page}
						</Dialog.Title>
						<Dialog.Description class="mt-1 text-[15px] leading-snug">
							{app.selected.text}
						</Dialog.Description>
					</div>
					<div class="flex shrink-0 items-center gap-4">
						{#if selectedUrl}
							<a
								href={selectedUrl}
								target="_blank"
								rel="noreferrer"
								class="cc-typed text-xs underline decoration-cv-teal-700 underline-offset-2"
								>open ↗</a
							>
						{/if}
						<Dialog.Close
							class="cc-typed border-2 border-cv-ink-950 px-3 py-1 text-xs font-bold hover:bg-cv-mint-50"
						>
							RETURN CARD
						</Dialog.Close>
					</div>
				</div>
				<div class="mx-7 mt-3 border-b-2 border-cv-teal-500"></div>
				<div class="min-h-0 flex-1 px-7 pt-4 pb-10">
					{#if selectedUrl}
						{#key selectedUrl}
							<iframe
								src={selectedUrl}
								title="Source page"
								class="h-full w-full border border-cv-ink-800/30 bg-cv-mint-50"
							></iframe>
						{/key}
					{:else}
						<p class="cc-typed text-sm">No source file catalogued for this card.</p>
					{/if}
				</div>
				<span class="cc-hole"></span>
			{/if}
		</Dialog.Content>
	</Dialog.Portal>
</Dialog.Root>

<style>
:global(.cc-root) {
	font-family: "Source Serif 4", Georgia, serif;
}
:global(.cc-typed) {
	font-family: "Courier Prime", "Courier New", monospace;
}
.plate {
	position: relative;
	border: 2px solid var(--color-cv-ink-800);
	background: white;
	box-shadow: inset 0 0 0 3px var(--color-cv-mint-50);
}
.screw {
	position: absolute;
	top: 50%;
	width: 5px;
	height: 5px;
	margin-top: -2.5px;
	border-radius: 9999px;
	background: var(--color-cv-ink-800);
}
.slip {
	border: 1px solid color-mix(in srgb, var(--color-cv-ink-800) 35%, transparent);
}
.ruled {
	background-image: repeating-linear-gradient(
		to bottom,
		transparent 0,
		transparent calc(1.5rem - 1px),
		color-mix(in srgb, var(--color-cv-teal-500) 30%, transparent) calc(1.5rem - 1px),
		color-mix(in srgb, var(--color-cv-teal-500) 30%, transparent) 1.5rem
	);
	background-attachment: local;
}
.file {
	font-size: 0.75rem;
	width: 100%;
}
.file::file-selector-button {
	margin-right: 0.5rem;
	border: 1px solid var(--color-cv-ink-800);
	background: var(--color-cv-mint-50);
	padding: 0.125rem 0.5rem;
	font-family: "Courier Prime", monospace;
}
:global(.cc-cabinet) {
	background: var(--color-cv-ink-950);
}
:global(.cc-drawer[data-state="inactive"]) {
	background: color-mix(in srgb, white 88%, var(--color-cv-ink-800));
	border-color: color-mix(in srgb, var(--color-cv-ink-800) 70%, transparent);
}
.holder {
	border: 2px solid var(--color-cv-ink-800);
	background: white;
	outline: 2px solid color-mix(in srgb, var(--color-cv-ink-800) 25%, transparent);
	outline-offset: 2px;
}
.pull {
	display: inline-block;
	width: 0.875rem;
	height: 0.875rem;
	border-radius: 9999px;
	border: 2px solid var(--color-cv-ink-800);
	background: var(--color-cv-mint-50);
}
.card {
	border: 1px solid color-mix(in srgb, var(--color-cv-ink-800) 35%, transparent);
	transition: transform 120ms;
}
.card-body {
	line-height: 1.5rem;
	background-image: repeating-linear-gradient(
		to bottom,
		transparent 0,
		transparent calc(1.5rem - 1px),
		color-mix(in srgb, var(--color-cv-teal-500) 22%, transparent) calc(1.5rem - 1px),
		color-mix(in srgb, var(--color-cv-teal-500) 22%, transparent) 1.5rem
	);
}
:global(.cc-hole) {
	position: absolute;
	bottom: 0.625rem;
	left: 50%;
	width: 0.875rem;
	height: 0.875rem;
	margin-left: -0.4375rem;
	border-radius: 9999px;
	background: var(--color-cv-mint-50);
	box-shadow: inset 0 1px 0 color-mix(in srgb, var(--color-cv-ink-950) 35%, transparent);
	border: 1px solid color-mix(in srgb, var(--color-cv-ink-800) 35%, transparent);
}
:global(.cc-pulled) {
	border: 1px solid var(--color-cv-ink-800);
	box-shadow: 8px 8px 0 var(--color-cv-ink-950);
}
:global(.cc-pulled .cc-hole) {
	width: 1.25rem;
	height: 1.25rem;
	margin-left: -0.625rem;
	bottom: 0.75rem;
}
</style>
