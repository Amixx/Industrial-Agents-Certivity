<script lang="ts">
import { Select } from 'bits-ui';
import { onMount } from 'svelte';
import { app } from '#lib/app.svelte.ts';

onMount(() => app.demo());

const selectedUrl = $derived(app.selected ? app.pdfUrl(app.selected.source) : null);
const total = $derived(app.result?.requirements.length ?? 0);
const date = new Date().toISOString().slice(0, 10);

const zonesX = ['1', '2', '3', '4', '5', '6', '7', '8'];
const zonesY = ['A', 'B', 'C', 'D', 'E', 'F'];

let dims = $state({ w: 1722, h: 1842 });
$effect(() => {
	const url = app.imageUrl;
	if (!url) return;
	const im = new Image();
	im.onload = () => (dims = { w: im.naturalWidth, h: im.naturalHeight });
	im.src = url;
});

const anchors = [
	[0.3, 0.28],
	[0.78, 0.33],
	[0.55, 0.2],
	[0.42, 0.72],
	[0.8, 0.8],
	[0.2, 0.6],
	[0.62, 0.5],
	[0.9, 0.12],
];

const plot = $derived.by(() => {
	const { w, h } = dims;
	const u = w / 36;
	const perRow = 4;
	const slot = w / perRow;
	const rowH = u * 4.2;
	const top = h + u * 3;
	const callouts = app.byRegulation.map((g, i) => {
		const [fx, fy] = anchors[i % anchors.length];
		const bx = (i % perRow) * slot + u * 1.6;
		const by = top + Math.floor(i / perRow) * rowH + u * 1.6;
		return { g, n: i + 1, ax: fx * w, ay: fy * h, bx, by };
	});
	const rows = Math.max(1, Math.ceil(callouts.length / perRow));
	return { w, h, u, callouts, viewBox: `${-u} ${-u} ${w + 2 * u} ${top + rows * rowH + u}` };
});

function selectRegulation(reg: string) {
	const first = app.byRegulation.find((g) => g.regulation === reg)?.requirements[0];
	if (first) app.select(first.id);
}
</script>

<svelte:head>
	<title>Drawing sheet</title>
	<link rel="preconnect" href="https://fonts.googleapis.com">
	<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous">
	<link
		rel="stylesheet"
		href="https://fonts.googleapis.com/css2?family=Overpass+Mono:wght@400;600&family=Share+Tech+Mono&display=swap"
	>
</svelte:head>

<svg width="0" height="0" class="absolute" aria-hidden="true">
	<filter id="sheet-linework" color-interpolation-filters="sRGB">
		<feColorMatrix
			type="matrix"
			values="0 0 0 0 0.475  0 0 0 0 0.949  0 0 0 0 0.871  -0.333 -0.333 -0.333 1 0"
		/>
	</filter>
</svg>

<div class="sheet h-screen min-h-[640px] bg-cv-ink-950 p-3 text-cv-mint-300">
	<div class="relative h-full border border-cv-mint-300/70 p-5">
		<div class="zone-row top-0">
			{#each zonesX as z (z)}
				<span>{z}</span>
			{/each}
		</div>
		<div class="zone-row bottom-0">
			{#each zonesX as z (z)}
				<span>{z}</span>
			{/each}
		</div>
		<div class="zone-col left-0">
			{#each zonesY as z (z)}
				<span>{z}</span>
			{/each}
		</div>
		<div class="zone-col right-0">
			{#each zonesY as z (z)}
				<span>{z}</span>
			{/each}
		</div>

		<div
			class="grid h-full grid-cols-[minmax(0,0.85fr)_minmax(0,1fr)_16rem] border-2 border-cv-mint-300 xl:grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)_22rem]"
		>
			<section class="flex min-h-0 flex-col border-r border-cv-mint-300">
				<div class="cell-head">
					<span>View A &mdash; exploded assembly</span>
					<span class="opacity-70 max-xl:hidden">Scale NTS &middot; 3rd angle</span>
				</div>
				<div class="relative min-h-0 flex-1 p-3">
					{#if app.imageUrl}
						<svg
							viewBox={plot.viewBox}
							preserveAspectRatio="xMidYMid meet"
							class="h-full w-full"
							role="img"
							aria-label="Exploded view with callouts to cited regulations"
						>
							<image
								href={app.imageUrl}
								width={plot.w}
								height={plot.h}
								filter="url(#sheet-linework)"
							/>
							{#each plot.callouts as c (c.g.regulation)}
								{@const active = app.selected?.source.regulation === c.g.regulation}
								{@const r = plot.u * 1.3}
								<g
									role="button"
									tabindex="0"
									class="callout cursor-pointer"
									class:active
									onclick={() => selectRegulation(c.g.regulation)}
									onkeydown={(e) => e.key === 'Enter' && selectRegulation(c.g.regulation)}
								>
									<line
										x1={c.ax}
										y1={c.ay}
										x2={c.bx}
										y2={c.by - r}
										stroke="currentColor"
										stroke-width={plot.u * 0.08}
									/>
									<circle cx={c.ax} cy={c.ay} r={plot.u * 0.28} fill="currentColor" />
									<circle
										cx={c.bx}
										cy={c.by}
										{r}
										class="balloon"
										stroke="currentColor"
										stroke-width={plot.u * 0.08}
									/>
									<text
										x={c.bx}
										y={c.by}
										text-anchor="middle"
										dominant-baseline="central"
										font-size={plot.u * 1.4}
										class="balloon-n"
									>
										{c.n}
									</text>
									<text x={c.bx + plot.u * 2} y={c.by - plot.u * 0.15} font-size={plot.u * 1.25}>
										{c.g.regulation}
									</text>
									<text
										x={c.bx + plot.u * 2}
										y={c.by + plot.u * 1.15}
										font-size={plot.u * 0.8}
										opacity="0.75"
									>
										QTY {c.g.count}
									</text>
								</g>
							{/each}
						</svg>
					{:else}
						<div
							class="flex h-full items-center justify-center border border-dashed border-cv-mint-300/40"
						>
							NO VIEW SUPPLIED
						</div>
					{/if}
					{#if app.loading}
						<div
							class="absolute top-4 left-4 bg-cv-ink-950 px-2 py-1 text-xs tracking-widest blink"
						>
							PLOTTING&hellip;
						</div>
					{/if}
				</div>
				<div class="border-t border-cv-mint-300">
					<div class="cell-head border-b-0">
						<span>Cited standards</span>
						<span class="opacity-70">{app.byRegulation.length} std &middot; {total} req</span>
					</div>
					<table class="w-full text-left text-[12px]">
						<thead class="text-[10px] tracking-widest opacity-70">
							<tr class="border-y border-cv-mint-300/40">
								<th class="w-12 px-2 py-0.5 font-normal">ITEM</th>
								<th class="w-24 px-2 py-0.5 font-normal">STANDARD</th>
								<th class="px-2 py-0.5 font-normal">TITLE</th>
								<th class="w-12 px-2 py-0.5 text-right font-normal">QTY</th>
							</tr>
						</thead>
						<tbody>
							{#each app.byRegulation as g, i (g.regulation)}
								<tr
									class="cursor-pointer border-b border-cv-mint-300/20 hover:bg-cv-mint-300/10"
									onclick={() => selectRegulation(g.regulation)}
								>
									<td class="px-2 py-1">{i + 1}</td>
									<td class="px-2 py-1 whitespace-nowrap">{g.regulation}</td>
									<td class="px-2 py-1 uppercase">{g.title}</td>
									<td class="px-2 py-1 text-right">{g.count}</td>
								</tr>
							{:else}
								<tr>
									<td colspan="4" class="px-2 py-1 opacity-60">&mdash;</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</section>

			<section class="flex min-h-0 flex-col border-r border-cv-mint-300">
				<form
					class="border-b border-cv-mint-300"
					onsubmit={(e) => {
						e.preventDefault();
						app.submit();
					}}
				>
					<div class="cell-head">
						<span>Notes &mdash; input</span>
						<span class="truncate opacity-70 max-xl:hidden">Case {app.selectedCase || '—'}</span>
					</div>
					<div class="grid grid-cols-[minmax(0,1fr)_auto] gap-x-3 gap-y-2 p-2">
						<div class="space-y-1.5">
							<Select.Root
								type="single"
								value={app.selectedCase}
								onValueChange={(v) => app.loadCase(v)}
								items={app.cases.map((c) => ({ value: c, label: c }))}
							>
								<Select.Trigger
									class="flex h-7 w-full items-center justify-between border border-cv-mint-300 px-2 text-[12px] tracking-wider uppercase hover:bg-cv-mint-300/10"
								>
									<span class="truncate"
										><span class="opacity-60">CASE /</span> {app.selectedCase || 'SELECT'}</span
									>
									<span aria-hidden="true">&#9660;</span>
								</Select.Trigger>
								<Select.Portal>
									<Select.Content
										sideOffset={2}
										class="sheet z-50 max-h-64 w-(--bits-select-anchor-width) overflow-auto border border-cv-mint-300 bg-cv-ink-950 text-[12px] text-cv-mint-300 uppercase"
									>
										<Select.Viewport>
											{#each app.cases as c (c)}
												<Select.Item
													value={c}
													label={c}
													class="cursor-default px-2 py-1 tracking-wider data-highlighted:bg-cv-mint-300 data-highlighted:text-cv-ink-950"
												>
													{c}
												</Select.Item>
											{/each}
										</Select.Viewport>
									</Select.Content>
								</Select.Portal>
							</Select.Root>
							<div class="grid grid-cols-2 gap-2 text-[10px] tracking-widest opacity-90">
								<label class="block">
									SPEC FILE
									<input
										type="file"
										accept=".md,.txt,text/*"
										onchange={(e) => app.setSpecFile(e.currentTarget.files?.[0])}
										class="file-input"
									>
								</label>
								<label class="block">
									VIEW IMAGE
									<input
										type="file"
										accept="image/*"
										onchange={(e) => app.setImageFile(e.currentTarget.files?.[0])}
										class="file-input"
									>
								</label>
							</div>
						</div>
						<div class="flex w-28 flex-col gap-1.5">
							<button
								type="submit"
								disabled={app.loading}
								class="h-7 bg-cv-mint-300 text-[12px] tracking-[0.2em] text-cv-ink-950 hover:bg-cv-teal-400 disabled:opacity-60"
							>
								{app.loading ? 'PLOTTING…' : 'RUN ▸'}
							</button>
							<button
								type="button"
								disabled={!app.result}
								onclick={() => app.download()}
								class="h-7 border border-cv-mint-300 text-[11px] tracking-[0.15em] hover:bg-cv-mint-300/10 disabled:opacity-40"
							>
								EXPORT JSON
							</button>
						</div>
						<textarea
							bind:value={app.spec}
							rows="4"
							aria-label="Product spec"
							class="body col-span-2 resize-y border border-cv-mint-300/50 bg-transparent p-1.5 text-[11.5px] leading-snug text-cv-mint-50 focus:border-cv-mint-300 focus:outline-none"
						></textarea>
						{#if app.error}
							<p class="col-span-2 border border-[#ff6b5e] px-2 py-1 text-[12px] text-[#ff6b5e]">
								&#9888; ERROR &mdash; {app.error}
							</p>
						{/if}
					</div>
				</form>

				<div class="cell-head">
					<span>Requirements schedule</span>
					<span class="opacity-70">{total} rows</span>
				</div>
				<div class="min-h-0 flex-1 overflow-auto">
					<table class="w-full border-collapse text-left text-[12px]">
						<thead class="sticky top-0 z-10 bg-cv-ink-950 text-[10px] tracking-widest">
							<tr class="border-b border-cv-mint-300">
								<th class="th w-20">REV / PARA</th>
								<th class="th">DESCRIPTION</th>
								<th class="th w-14">ISS</th>
								<th class="th w-10 text-right">SHT</th>
							</tr>
						</thead>
						{#each app.byRegulation as g, i (g.regulation)}
							<tbody>
								<tr class="border-b border-cv-mint-300/40 bg-cv-mint-300/10">
									<th
										colspan="4"
										class="px-2 py-1 text-[11px] font-normal tracking-widest uppercase"
									>
										<span
											class="mr-1 inline-flex h-4 w-4 items-center justify-center rounded-full border border-cv-mint-300 text-[10px]"
											>{i + 1}</span
										>
										{g.regulation}
										&mdash; {g.title}
										<span class="opacity-60">/ {g.count}</span>
									</th>
								</tr>
								{#each g.requirements as req (req.id)}
									{@const url = app.pdfUrl(req.source)}
									{@const sel = app.selectedId === req.id}
									<tr
										onclick={() => app.select(req.id)}
										class="cursor-pointer border-b border-cv-mint-300/20 align-top {sel
											? 'bg-cv-mint-300 text-cv-ink-950'
											: 'hover:bg-cv-mint-300/10'}"
									>
										<td class="td whitespace-nowrap">
											{req.id}
											<div class="opacity-70">&para; {req.source.paragraph ?? '—'}</div>
										</td>
										<td
											class="td body text-[11.5px] leading-snug {sel ? '' : 'text-cv-mint-50/90'}"
										>
											{req.text}
										</td>
										<td class="td whitespace-nowrap">{req.source.version}</td>
										<td class="td text-right">
											{#if url}
												<a
													href={url}
													target="_blank"
													rel="noreferrer"
													onclick={(e) => e.stopPropagation()}
													class="underline underline-offset-2"
													>{req.source.page}</a
												>
											{:else}
												{req.source.page}
											{/if}
										</td>
									</tr>
								{/each}
							</tbody>
						{/each}
					</table>
					{#if !app.byRegulation.length}
						<p class="p-3 text-[12px] opacity-60">
							{app.loading ? 'PLOTTING…' : 'NO ROWS. RUN TO GENERATE SCHEDULE.'}
						</p>
					{/if}
				</div>
			</section>

			<section class="flex min-h-0 flex-col">
				<div class="cell-head">
					<span>Detail B &mdash; source</span>
					{#if app.selected && selectedUrl}
						<a href={selectedUrl} target="_blank" rel="noreferrer" class="underline"
							>OPEN &#8599;</a
						>
					{/if}
				</div>
				{#if app.selected && selectedUrl}
					<div class="border-b border-cv-mint-300/40 px-2 py-1 text-[11px] tracking-wider">
						{app.selected.id}
						&middot; {app.selected.source.regulation} ISS {app.selected.source.version}
						&middot; &para; {app.selected.source.paragraph ?? '—'} &middot; SHT
						{app.selected.source.page}
					</div>
					<div class="min-h-0 flex-1 bg-white">
						{#key selectedUrl}
							<iframe src={selectedUrl} title="Source page" class="h-full w-full border-0"></iframe>
						{/key}
					</div>
				{:else}
					<div
						class="relative m-3 flex flex-1 items-center justify-center border border-dashed border-cv-mint-300/40 text-center text-[12px] leading-relaxed tracking-wider opacity-80"
					>
						<span class="crosshair"></span>
						<span class="relative bg-cv-ink-950 px-2"
							>SELECT A SCHEDULE ROW<br>TO PROJECT ITS SOURCE PAGE</span
						>
					</div>
				{/if}

				<div
					class="title-block grid grid-cols-[1fr_auto] border-t-2 border-cv-mint-300 text-[10px] tracking-widest"
				>
					<div
						class="col-span-2 flex items-end justify-between border-b border-cv-mint-300 px-2 pt-1 pb-1.5"
					>
						<div>
							<div class="opacity-60">PROJECT</div>
							<div class="wordmark">sudo</div>
						</div>
						<div class="pb-1 text-right">
							<div class="opacity-60">IN COLLABORATION WITH</div>
							<div class="text-[13px] tracking-[0.2em]">CERTIVITY</div>
						</div>
					</div>
					<div class="border-r border-b border-cv-mint-300 px-2 py-1">
						<div class="opacity-60">CASE</div>
						<div class="truncate text-[12px] uppercase">{app.selectedCase || '—'}</div>
					</div>
					<div class="border-b border-cv-mint-300 px-2 py-1">
						<div class="opacity-60">DATE</div>
						<div class="text-[12px]">{date}</div>
					</div>
					<div class="border-r border-cv-mint-300 px-2 py-1">
						<div class="opacity-60">DWG / REQ</div>
						<div class="text-[12px]">SUDO-{String(total).padStart(4, '0')}</div>
					</div>
					<div class="flex items-end justify-between gap-3 px-2 py-1">
						<div>
							<div class="opacity-60">SHEET</div>
							<div class="text-[12px]">1 OF 1</div>
						</div>
						<a href="/v" class="pb-0.5 underline opacity-80">INDEX</a>
					</div>
				</div>
			</section>
		</div>
	</div>
</div>

<style>
:global(.sheet) {
	font-family: "Share Tech Mono", ui-monospace, monospace;
}
.body {
	font-family: "Overpass Mono", ui-monospace, monospace;
}
.zone-row {
	position: absolute;
	left: 1.25rem;
	right: 1.25rem;
	display: flex;
	height: 1.25rem;
	font-size: 11px;
}
.zone-row span {
	flex: 1;
	display: flex;
	align-items: center;
	justify-content: center;
	border-left: 1px solid color-mix(in srgb, var(--color-cv-mint-300) 50%, transparent);
}
.zone-row span:first-child {
	border-left: 0;
}
.zone-col {
	position: absolute;
	top: 1.25rem;
	bottom: 1.25rem;
	display: flex;
	flex-direction: column;
	width: 1.25rem;
	font-size: 11px;
}
.zone-col span {
	flex: 1;
	display: flex;
	align-items: center;
	justify-content: center;
	border-top: 1px solid color-mix(in srgb, var(--color-cv-mint-300) 50%, transparent);
}
.zone-col span:first-child {
	border-top: 0;
}
.cell-head {
	display: flex;
	justify-content: space-between;
	gap: 1rem;
	white-space: nowrap;
	border-bottom: 1px solid var(--color-cv-mint-300);
	padding: 0.2rem 0.5rem;
	font-size: 11px;
	letter-spacing: 0.18em;
	text-transform: uppercase;
}
.th {
	padding: 0.25rem 0.5rem;
	font-weight: 400;
}
.td {
	padding: 0.3rem 0.5rem;
}
.file-input {
	display: block;
	width: 100%;
	margin-top: 0.15rem;
	font-size: 10px;
	letter-spacing: 0;
}
.file-input::file-selector-button {
	margin-right: 0.4rem;
	border: 1px solid var(--color-cv-mint-300);
	background: transparent;
	padding: 0.05rem 0.4rem;
	font:
		10px "Share Tech Mono",
		monospace;
	letter-spacing: 0.1em;
	color: var(--color-cv-mint-300);
}
.callout {
	color: var(--color-cv-mint-300);
	fill: var(--color-cv-mint-300);
	font-family: "Share Tech Mono", monospace;
	outline: none;
}
.callout .balloon {
	fill: var(--color-cv-ink-950);
}
.callout.active,
.callout:hover,
.callout:focus-visible {
	color: var(--color-cv-teal-400);
	fill: var(--color-cv-teal-400);
}
.callout.active .balloon {
	fill: var(--color-cv-mint-300);
}
.callout.active .balloon-n {
	fill: var(--color-cv-ink-950);
}
.wordmark {
	font-size: 2.6rem;
	line-height: 0.9;
	letter-spacing: 0.04em;
}
.crosshair {
	position: absolute;
	inset: 0;
	background:
		linear-gradient(var(--color-cv-mint-300), var(--color-cv-mint-300)) center / 1px 100% no-repeat,
		linear-gradient(var(--color-cv-mint-300), var(--color-cv-mint-300)) center / 100% 1px no-repeat;
	opacity: 0.25;
}
.blink {
	animation: blink 1s steps(2) infinite;
}
@keyframes blink {
	50% {
		opacity: 0.2;
	}
}
</style>
