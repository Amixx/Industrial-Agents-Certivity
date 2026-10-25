<script lang="ts">
import { Select } from 'bits-ui';
import { onMount } from 'svelte';
import { app } from '#lib/app.svelte.ts';

onMount(() => app.demo());

const selectedUrl = $derived(app.selected ? app.pdfUrl(app.selected.source) : null);
const total = $derived(app.result?.requirements.length ?? 0);
const today = new Date().toLocaleDateString('en-GB', {
	weekday: 'long',
	day: 'numeric',
	month: 'long',
	year: 'numeric',
});
const sectionLetter = (i: number) => String.fromCharCode(65 + i);
const anchor = (reg: string) => `sec-${reg.replace(/\W+/g, '-')}`;
const plural = (n: number, word: string) => `${n} ${word}${n === 1 ? '' : 's'}`;
</script>

<svelte:head>
	<title>Gazette</title>
	<link rel="preconnect" href="https://fonts.googleapis.com">
	<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous">
	<link
		rel="stylesheet"
		href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400..900;1,9..144,400..700&family=Newsreader:ital,opsz,wght@0,6..72,400..700;1,6..72,400..600&display=swap"
	>
</svelte:head>

<div class="gazette min-h-screen bg-cv-mint-50 text-cv-ink-800">
	<div class="mx-auto max-w-[1600px] px-6">
		<div
			class="flex items-baseline justify-between border-b border-cv-ink-800 py-1.5 text-[12px] tracking-[0.08em] uppercase"
		>
			<span>Vol. I &middot; No. {total || '—'}</span>
			<span class="italic normal-case tracking-normal">in collaboration with Certivity</span>
			<span class="flex gap-4">
				<span>{today}</span>
				<a href="/v" class="underline decoration-1 underline-offset-2">All variants</a>
			</span>
		</div>

		<header class="grid grid-cols-[13rem_1fr_13rem] items-center gap-6 py-3">
			<div class="ear">
				<div class="kicker">Today&rsquo;s case</div>
				<div class="font-display text-lg leading-tight font-semibold">
					{app.selectedCase || '—'}
				</div>
				<div class="text-[13px] italic">one of {plural(app.cases.length, 'case')} on file</div>
			</div>
			<div class="text-center">
				<h1 class="nameplate">sudo</h1>
				<p class="-mt-1 text-[14px] italic">
					&ldquo;All the requirements that are fit to cite.&rdquo;
				</p>
			</div>
			<div class="ear text-right">
				<div class="kicker">This edition</div>
				<div class="font-display text-lg leading-tight font-semibold">
					{plural(total, 'requirement')}
				</div>
				<div class="text-[13px] italic">
					from {plural(app.byRegulation.length, 'UN Regulation')}
				</div>
			</div>
		</header>
		<div class="border-t-[5px] border-double border-cv-ink-800"></div>
		<div class="mt-[3px] border-t border-cv-ink-800"></div>

		<div
			class="grid grid-cols-[14rem_minmax(0,1fr)_19rem] xl:grid-cols-[17rem_minmax(0,1fr)_27rem]"
		>
			<aside class="sticky top-0 h-screen overflow-y-auto border-r border-cv-ink-800/60 py-4 pr-5">
				<div class="kicker">The desk</div>
				<h2 class="font-display mb-3 text-2xl leading-tight font-bold">Filed copy</h2>

				<form
					class="space-y-3"
					onsubmit={(e) => {
						e.preventDefault();
						app.submit();
					}}
				>
					<div>
						<div class="label">Case</div>
						<Select.Root
							type="single"
							value={app.selectedCase}
							onValueChange={(v) => app.loadCase(v)}
							items={app.cases.map((c) => ({ value: c, label: c }))}
						>
							<Select.Trigger
								class="flex w-full items-baseline justify-between border-y border-cv-ink-800 bg-white px-1 py-1 text-left text-[15px]"
							>
								<span class="italic">{app.selectedCase || 'Choose a case'}</span>
								<span aria-hidden="true" class="text-xs">&#9662;</span>
							</Select.Trigger>
							<Select.Portal>
								<Select.Content
									sideOffset={2}
									class="gazette z-50 max-h-64 w-(--bits-select-anchor-width) overflow-auto border border-cv-ink-800 bg-white text-[15px] text-cv-ink-800"
								>
									<Select.Viewport>
										{#each app.cases as c (c)}
											<Select.Item
												value={c}
												label={c}
												class="cursor-default border-b border-cv-ink-800/20 px-2 py-1 italic data-highlighted:bg-cv-mint-300/50 data-selected:font-semibold"
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
						<span class="label">Product specification</span>
						<textarea
							bind:value={app.spec}
							rows="7"
							class="block w-full resize-y border-y border-cv-ink-800 bg-white px-1 py-1 text-[13px] leading-snug"
						></textarea>
					</label>
					<label class="block">
						<span class="label">Or set from a file</span>
						<input
							type="file"
							accept=".md,.txt,text/*"
							onchange={(e) => app.setSpecFile(e.currentTarget.files?.[0])}
							class="file-input"
						>
					</label>

					<figure>
						<div
							class="flex h-28 items-center justify-center border border-cv-ink-800 bg-white p-2"
						>
							{#if app.imageUrl}
								<img
									src={app.imageUrl}
									alt="Exploded view"
									class="max-h-full max-w-full object-contain"
								>
							{:else}
								<span class="text-sm italic opacity-60">No illustration filed</span>
							{/if}
						</div>
						<figcaption class="mt-1 text-[12px] italic">
							Fig. 1 &mdash; Exploded view, as submitted.
						</figcaption>
					</figure>
					<input
						type="file"
						accept="image/*"
						aria-label="Exploded view image"
						onchange={(e) => app.setImageFile(e.currentTarget.files?.[0])}
						class="file-input -mt-2"
					>

					<div class="space-y-2 border-t border-cv-ink-800 pt-3">
						<button
							type="submit"
							disabled={app.loading}
							class="font-display w-full bg-cv-ink-800 py-2 text-[15px] font-semibold tracking-[0.12em] text-cv-mint-50 uppercase hover:bg-cv-ink-950 disabled:opacity-70"
						>
							{app.loading ? 'Setting type…' : 'Run the edition'}
						</button>
						<button
							type="button"
							disabled={!app.result}
							onclick={() => app.download()}
							class="w-full border border-cv-ink-800 py-1.5 text-[13px] italic hover:bg-white disabled:opacity-40"
						>
							Download this edition (JSON)
						</button>
					</div>
					{#if app.error}
						<p class="border-l-2 border-[#b3261e] pl-2 text-[13px] text-[#b3261e]">
							<span class="font-semibold tracking-wider uppercase">Correction.</span>
							{app.error}
						</p>
					{/if}
				</form>
			</aside>

			<main class="min-w-0 px-7 py-4">
				{#if app.byRegulation.length}
					<div class="kicker">Front page &middot; {app.selectedCase}</div>
					<h2
						class="font-display mt-1 text-[clamp(2rem,3.2vw,2.75rem)] leading-[1.02] font-bold tracking-tight"
					>
						{plural(total, 'requirement')}
						cited against
						{app.byRegulation.map((g) => g.regulation).join(', ')}
					</h2>
					<p class="mt-2 text-[19px] leading-snug italic">
						Every paragraph below is quoted from the regulation and printed with the page it came
						from. Select one to read the source alongside.
					</p>

					<nav class="mt-5 border-y border-cv-ink-800 py-2">
						<div class="kicker mb-1">In this edition</div>
						<ul class="grid grid-cols-[repeat(auto-fill,minmax(min(18rem,100%),1fr))] gap-x-8">
							{#each app.byRegulation as g, i (g.regulation)}
								<li>
									<a href="#{anchor(g.regulation)}" class="index-row group">
										<span class="font-display font-semibold">{sectionLetter(i)}</span>
										<span class="group-hover:underline">
											<span class="font-semibold">{g.regulation}</span>
											<span class="italic">{g.title}</span>
										</span>
										<span class="leader"></span>
										<span class="font-display font-semibold tabular-nums">{g.count}</span>
									</a>
								</li>
							{/each}
						</ul>
					</nav>

					{#each app.byRegulation as g, i (g.regulation)}
						<section id={anchor(g.regulation)} class="mt-7 scroll-mt-4">
							<div class="border-t-[3px] border-cv-ink-800 pt-1">
								<div class="kicker">Section {sectionLetter(i)}</div>
								<div class="flex items-baseline justify-between gap-4">
									<h3 class="font-display text-[32px] leading-tight font-bold">
										{g.regulation}
										<span class="font-normal italic">&mdash; {g.title}</span>
									</h3>
									<span class="shrink-0 text-[13px] tracking-[0.08em] uppercase">
										{plural(g.count, 'requirement')}
									</span>
								</div>
							</div>
							<div class="cols mt-3 border-t border-cv-ink-800/60 pt-3">
								{#each g.requirements as req (req.id)}
									{@const url = app.pdfUrl(req.source)}
									<div
										role="button"
										tabindex="0"
										aria-pressed={app.selectedId === req.id}
										onclick={() => app.select(req.id)}
										onkeydown={(e) => {
											if (e.key === 'Enter' || e.key === ' ') {
												e.preventDefault();
												app.select(req.id);
											}
										}}
										class="item {app.selectedId === req.id ? 'is-selected' : ''}"
									>
										<span class="drop">{req.source.paragraph ?? '§'}</span>
										<p class="text">{req.text}</p>
										<p class="byline">
											{req.id}
											&middot; {req.source.regulation} rev. {req.source.version} &middot;
											{#if url}
												<a
													href={url}
													target="_blank"
													rel="noreferrer"
													onclick={(e) => e.stopPropagation()}
													class="underline decoration-1 underline-offset-2"
													>page {req.source.page}</a
												>
											{:else}
												page {req.source.page}
											{/if}
										</p>
									</div>
								{/each}
							</div>
						</section>
					{/each}
				{:else}
					<div class="py-16 text-center">
						<div class="kicker">Front page</div>
						<p class="font-display mt-2 text-4xl font-bold">
							{app.loading ? 'Stop the presses: setting type…' : 'No edition yet.'}
						</p>
						<p class="mt-2 italic">File a case on the left and run the edition.</p>
					</div>
				{/if}
			</main>

			<aside class="sticky top-0 flex h-screen flex-col border-l border-cv-ink-800/60 py-4 pl-5">
				<div class="kicker">Sidebar &middot; from the source</div>
				{#if app.selected && selectedUrl}
					<h2 class="font-display text-2xl leading-tight font-bold">
						{app.selected.source.regulation}, page {app.selected.source.page}
					</h2>
					<p class="text-[13px] tracking-[0.06em] uppercase">
						Paragraph {app.selected.source.paragraph ?? '—'} &middot; revision
						{app.selected.source.version}
						&middot; {app.selected.id}
					</p>
					<blockquote
						class="my-3 line-clamp-4 border-y border-cv-ink-800 py-2 text-[16px] leading-snug italic"
					>
						&ldquo;{app.selected.text}&rdquo;
					</blockquote>
					{#key selectedUrl}
						<iframe
							src={selectedUrl}
							title="Source page"
							class="min-h-0 w-full flex-1 border border-cv-ink-800 bg-white"
						></iframe>
					{/key}
					<a
						href={selectedUrl}
						target="_blank"
						rel="noreferrer"
						class="mt-1 self-end text-[12px] italic underline"
						>Continued in a new tab</a
					>
				{:else}
					<h2 class="font-display text-2xl leading-tight font-bold">The source, in full</h2>
					<p class="mt-2 text-[15px] leading-snug italic">
						Select any paragraph in the paper and its page from the regulation is printed here,
						beside the story.
					</p>
					<div
						class="mt-4 flex flex-1 items-center justify-center border border-dashed border-cv-ink-800/50"
					>
						<span class="font-display text-7xl opacity-15">&sect;</span>
					</div>
				{/if}
			</aside>
		</div>
	</div>
</div>

<style>
:global(.gazette) {
	font-family: "Newsreader", Georgia, serif;
	font-optical-sizing: auto;
}
.font-display {
	font-family: "Fraunces", Georgia, serif;
	font-optical-sizing: auto;
}
.nameplate {
	font-family: "Fraunces", Georgia, serif;
	font-size: clamp(5rem, 9vw, 8.5rem);
	font-weight: 900;
	font-variation-settings:
		"opsz" 144,
		"SOFT" 0,
		"WONK" 1;
	line-height: 0.9;
	letter-spacing: -0.04em;
}
.ear {
	border: 1px solid var(--color-cv-ink-800);
	padding: 0.5rem 0.75rem;
}
.kicker {
	font-size: 11px;
	font-weight: 600;
	letter-spacing: 0.16em;
	text-transform: uppercase;
	color: var(--color-cv-teal-700);
}
.label {
	display: block;
	margin-bottom: 0.2rem;
	font-size: 11px;
	letter-spacing: 0.14em;
	text-transform: uppercase;
}
.file-input {
	display: block;
	width: 100%;
	font-size: 12px;
}
.file-input::file-selector-button {
	margin-right: 0.5rem;
	border: 1px solid var(--color-cv-ink-800);
	background: white;
	padding: 0.1rem 0.5rem;
	font:
		italic 12px "Newsreader",
		serif;
	color: var(--color-cv-ink-800);
}
.index-row {
	display: flex;
	align-items: baseline;
	gap: 0.5rem;
	padding: 0.15rem 0;
	font-size: 15px;
}
.leader {
	flex: 1;
	border-bottom: 1px dotted var(--color-cv-ink-800);
	transform: translateY(-0.25em);
}
.cols {
	column-width: 16rem;
	column-gap: 2.25rem;
	column-rule: 1px solid color-mix(in srgb, var(--color-cv-ink-800) 45%, transparent);
}
.item {
	break-inside: avoid;
	margin: 0 -0.5rem 0.9rem;
	padding: 0.35rem 0.5rem 0.5rem;
	cursor: pointer;
	border-bottom: 1px solid color-mix(in srgb, var(--color-cv-ink-800) 20%, transparent);
}
.item:hover {
	background: white;
}
.item.is-selected {
	background: color-mix(in srgb, var(--color-cv-mint-300) 40%, white);
	box-shadow: inset 3px 0 0 var(--color-cv-ink-800);
}
.item:focus-visible {
	outline: 1px solid var(--color-cv-ink-800);
}
.drop {
	float: left;
	margin: 0.2rem 0.5rem 0 0;
	padding-right: 0.5rem;
	border-right: 1px solid var(--color-cv-ink-800);
	font-family: "Fraunces", serif;
	font-size: 1.85rem;
	font-weight: 800;
	font-variation-settings: "opsz" 72;
	line-height: 0.95;
	letter-spacing: -0.03em;
	font-variant-numeric: lining-nums;
}
.text {
	font-size: 15.5px;
	line-height: 1.42;
	text-align: justify;
	hyphens: auto;
}
.byline {
	clear: both;
	margin-top: 0.3rem;
	font-size: 11.5px;
	letter-spacing: 0.08em;
	text-transform: uppercase;
	color: var(--color-cv-teal-700);
}
</style>
