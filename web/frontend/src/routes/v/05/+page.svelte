<script lang="ts">
import { Select } from 'bits-ui';
import { onMount } from 'svelte';
import { app } from '#lib/app.svelte.ts';

onMount(() => app.demo());

const selectedUrl = $derived(app.selected ? app.pdfUrl(app.selected.source) : null);
const total = $derived(app.result?.requirements.length ?? 0);
const pad = (n: number) => String(n).padStart(2, '0');
</script>

<svelte:head>
	<title>sudo — Swiss grid</title>
	<link rel="preconnect" href="https://fonts.googleapis.com">
	<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous">
	<link
		rel="stylesheet"
		href="https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@300;400;500;600;700;800&display=swap"
	>
</svelte:head>

<div class="sw-root min-h-screen bg-white text-black">
	<div class="grid grid-cols-12 gap-x-4 px-8 xl:gap-x-6 xl:px-12">
		<header
			class="col-span-12 grid grid-cols-12 gap-x-4 border-t-[6px] border-black pt-4 xl:gap-x-6"
		>
			<h1
				class="col-span-7 text-[10rem] leading-[0.78] font-bold tracking-[-0.06em] xl:text-[14rem]"
			>
				sudo
			</h1>
			<div class="col-span-5 flex flex-col justify-between pb-2">
				<nav class="flex justify-between text-xs font-medium">
					<span>{app.result?.case_id ?? '—'}</span>
					<a href="/v" class="hover:underline">All variants</a>
				</nav>
				<div>
					<p class="max-w-[28ch] text-xl leading-tight font-medium">
						Requirements under UN Regulations, each cited to its source page.
					</p>
					<p class="mt-3 text-xs">In collaboration with <span class="font-bold">Certivity</span></p>
				</div>
			</div>
		</header>

		<form
			class="col-span-12 mt-12 grid grid-cols-12 gap-x-4 border-t border-black pt-3 xl:gap-x-6"
			onsubmit={(e) => {
				e.preventDefault();
				app.submit();
			}}
		>
			<div class="col-span-2">
				<div class="text-5xl leading-none font-light text-cv-teal-700">1</div>
				<div class="mt-2 text-sm font-bold">Input</div>
			</div>

			<div class="col-span-3 flex flex-col gap-5">
				<div>
					<div class="label">Case</div>
					<Select.Root
						type="single"
						value={app.selectedCase}
						onValueChange={(v) => app.loadCase(v)}
						items={app.cases.map((c) => ({ value: c, label: c }))}
					>
						<Select.Trigger
							class="flex h-9 w-full items-center justify-between border-b-2 border-black text-left text-base font-medium"
						>
							{app.selectedCase || 'Select case'}
							<span aria-hidden="true" class="text-xs">↓</span>
						</Select.Trigger>
						<Select.Portal>
							<Select.Content
								sideOffset={0}
								class="sw-root z-50 max-h-64 w-(--bits-select-anchor-width) overflow-auto border-2 border-t-0 border-black bg-white text-sm"
							>
								<Select.Viewport>
									{#each app.cases as c (c)}
										<Select.Item
											value={c}
											label={c}
											class="flex cursor-default items-center gap-2 px-2 py-2 data-highlighted:bg-black data-highlighted:text-white"
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
					<span class="label">Spec file</span>
					<input
						type="file"
						accept=".md,.txt,text/*"
						onchange={(e) => app.setSpecFile(e.currentTarget.files?.[0])}
						class="file"
					>
				</label>
				<label class="block">
					<span class="label">Exploded view</span>
					<input
						type="file"
						accept="image/*"
						onchange={(e) => app.setImageFile(e.currentTarget.files?.[0])}
						class="file"
					>
				</label>
			</div>

			<label class="col-span-4 flex flex-col">
				<span class="label">Product spec</span>
				<textarea
					bind:value={app.spec}
					rows="9"
					class="min-h-0 flex-1 resize-none border-y-2 border-black py-2 pb-3 text-[13px] leading-snug outline-none focus:bg-cv-mint-50"
				></textarea>
			</label>

			<div class="col-span-3 flex flex-col">
				<span class="label">Drawing</span>
				<div class="flex h-36 items-center justify-center border-t-2 border-black">
					{#if app.imageUrl}
						<img src={app.imageUrl} alt="Exploded view" class="max-h-32 max-w-full object-contain">
					{:else}
						<span class="text-xs">No drawing</span>
					{/if}
				</div>
				<div class="mt-auto grid grid-cols-2 gap-x-4 xl:gap-x-6">
					<button
						type="submit"
						disabled={app.loading}
						class="flex h-11 items-center justify-between bg-black px-3 text-sm font-bold text-white disabled:bg-cv-ink-800"
					>
						{#if app.loading}
							Running
							<span class="size-2 animate-pulse bg-cv-mint-300"></span>
						{:else}
							Run <span aria-hidden="true">→</span>
						{/if}
					</button>
					<button
						type="button"
						disabled={!app.result}
						onclick={() => app.download()}
						class="flex h-11 items-center justify-between border-2 border-black px-3 text-sm font-bold disabled:opacity-30"
					>
						JSON <span aria-hidden="true">↓</span>
					</button>
				</div>
			</div>

			{#if app.error}
				<p
					class="col-span-10 col-start-3 mt-4 border-t-2 border-red-600 pt-2 text-sm font-medium text-red-600"
				>
					Error — {app.error}
				</p>
			{/if}
		</form>

		<section
			class="col-span-12 mt-12 grid grid-cols-12 gap-x-4 border-t border-black pt-3 xl:gap-x-6"
		>
			<div class="col-span-2">
				<div class="text-5xl leading-none font-light text-cv-teal-700">2</div>
				<div class="mt-2 text-sm font-bold">Regulations cited</div>
			</div>
			<div class="col-span-2">
				<div class="text-7xl leading-[0.85] font-bold tracking-tight text-cv-teal-700 tabular-nums">
					{pad(total)}
				</div>
				<div class="mt-2 text-xs">requirements in total</div>
			</div>
			<ol class="col-span-8 grid grid-cols-4 gap-x-4 gap-y-6 xl:gap-x-6">
				{#each app.byRegulation as g (g.regulation)}
					<li class="border-t-2 border-black pt-2">
						<div class="text-4xl leading-none font-light text-cv-teal-700 tabular-nums">
							{pad(g.count)}
						</div>
						<div class="mt-2 text-sm font-bold">{g.regulation}</div>
						<div class="text-xs leading-snug">{g.title}</div>
					</li>
				{:else}
					<li class="col-span-4 text-sm">{app.loading ? 'Running…' : 'No results yet.'}</li>
				{/each}
			</ol>
		</section>

		<section
			class="col-span-12 mt-12 grid grid-cols-12 gap-x-4 border-t border-black pt-3 pb-16 xl:gap-x-6"
		>
			<div class="col-span-7 grid grid-cols-7 content-start gap-x-4 xl:gap-x-6">
				<div class="col-span-2">
					<div class="text-5xl leading-none font-light text-cv-teal-700">3</div>
					<div class="mt-2 text-sm font-bold">Requirements</div>
				</div>
				<div class="col-span-5 self-end text-xs">
					Paragraph · requirement · source. Select a row to read its page.
				</div>

				{#each app.byRegulation as g (g.regulation)}
					<h2
						class="col-span-7 mt-10 grid grid-cols-7 gap-x-4 border-b-2 border-black pb-1 xl:gap-x-6"
					>
						<span class="col-span-2 text-sm font-bold">{g.regulation}</span>
						<span class="col-span-5 flex justify-between text-sm">
							<span class="font-medium">{g.title}</span>
							<span class="tabular-nums">{pad(g.count)}</span>
						</span>
					</h2>
					{#each g.requirements as req (req.id)}
						{@const url = app.pdfUrl(req.source)}
						{@const active = app.selectedId === req.id}
						<div
							role="button"
							tabindex="0"
							onclick={() => app.select(req.id)}
							onkeydown={(e) => (e.key === 'Enter' || e.key === ' ') && app.select(req.id)}
							class="group col-span-7 grid cursor-pointer grid-cols-7 gap-x-4 border-b border-black/15 py-3 outline-none xl:gap-x-6"
						>
							<div class="relative col-span-2">
								{#if active}
									<span
										class="absolute top-1.5 -left-5 size-2.5 bg-cv-mint-300 ring-1 ring-black"
									></span>
								{/if}
								<span
									class="text-2xl leading-none font-light tracking-tight text-cv-teal-700 tabular-nums group-hover:font-normal"
								>
									{req.source.paragraph ?? '—'}
								</span>
							</div>
							<div class="col-span-5">
								<p class="text-[15px] leading-snug {active ? 'font-medium' : ''}">{req.text}</p>
								<div class="mt-2 flex gap-5 text-xs">
									<span class="font-bold">{req.id}</span>
									<span>{req.source.regulation} {req.source.version}</span>
									{#if url}
										<a
											href={url}
											target="_blank"
											rel="noreferrer"
											onclick={(e) => e.stopPropagation()}
											class="underline decoration-1 underline-offset-2 hover:text-cv-teal-700"
											>Page {req.source.page} ↗</a
										>
									{:else}
										<span>Page {req.source.page}</span>
									{/if}
								</div>
							</div>
						</div>
					{/each}
				{/each}
			</div>

			<aside class="col-span-5 self-start lg:sticky lg:top-0">
				<div class="flex h-screen flex-col py-3">
					<div class="flex items-end justify-between border-b-2 border-black pb-2">
						<div>
							<div class="text-sm font-bold">Source page</div>
							{#if app.selected}
								<div class="text-xs">
									{app.selected.id}
									· {app.selected.source.regulation}
									{app.selected.source.version}
									· §{app.selected.source.paragraph ?? '—'}
								</div>
							{/if}
						</div>
						{#if app.selected}
							<div class="text-5xl leading-none font-light text-cv-teal-700 tabular-nums">
								p{app.selected.source.page}
							</div>
						{/if}
					</div>
					{#if app.selected && selectedUrl}
						{#key selectedUrl}
							<iframe
								src={selectedUrl}
								title="Source page"
								class="min-h-0 flex-1 border-0 bg-white"
							></iframe>
						{/key}
						<a
							href={selectedUrl}
							target="_blank"
							rel="noreferrer"
							class="border-t border-black pt-2 text-xs font-medium hover:underline"
							>Open in new tab ↗</a
						>
					{:else}
						<div class="flex flex-1 flex-col justify-start pt-6">
							<p class="max-w-[22ch] text-3xl leading-tight font-light">
								Select a requirement to show its source page here.
							</p>
						</div>
					{/if}
				</div>
			</aside>
		</section>
	</div>
</div>

<style>
:global(.sw-root) {
	font-family: "Hanken Grotesk", "Helvetica Neue", Arial, sans-serif;
	font-feature-settings:
		"ss01",
		"tnum" 0;
}
.label {
	display: block;
	margin-bottom: 0.25rem;
	font-size: 0.6875rem;
	font-weight: 700;
}
.file {
	display: block;
	width: 100%;
	border-bottom: 1px solid black;
	padding-bottom: 0.375rem;
	font-size: 0.75rem;
}
.file::file-selector-button {
	margin-right: 0.5rem;
	border: 0;
	background: black;
	color: white;
	padding: 0.25rem 0.5rem;
	font: inherit;
	font-weight: 700;
}
</style>
