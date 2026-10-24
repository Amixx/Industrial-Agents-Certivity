<script lang="ts">
	import { onMount } from 'svelte';
	import { SvelteSet } from 'svelte/reactivity';
	import { Checkbox, Select } from 'bits-ui';
	import { app } from '#lib/app.svelte.ts';

	onMount(() => app.demo());

	const reviewed = new SvelteSet<string>();
	const selectedUrl = $derived(app.selected ? app.pdfUrl(app.selected.source) : null);
	const total = $derived(app.result?.requirements.length ?? 0);
	const today = new Date().toISOString().slice(0, 10);

	function pagesCited(reqs: { source: { page: number } }[]) {
		return [...new Set(reqs.map((r) => r.source.page))].sort((a, b) => a - b).join(', ');
	}

	function toggle(id: string, on: boolean) {
		if (on) reviewed.add(id);
		else reviewed.delete(id);
	}
</script>

<svelte:head>
	<title>Audit report</title>
	<link rel="preconnect" href="https://fonts.googleapis.com" />
	<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous" />
	<link
		rel="stylesheet"
		href="https://fonts.googleapis.com/css2?family=Public+Sans:wght@400;500;600;700&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;0,8..60,700;1,8..60,400&display=swap"
	/>
</svelte:head>

<div class="flex h-screen bg-cv-ink-800/10 font-['Source_Serif_4'] text-[15px] text-black">
	<main class="min-w-0 flex-1 overflow-auto px-4 py-6 xl:px-8 xl:py-8">
		<article class="mx-auto max-w-[960px] border border-black/25 bg-white">
			<header class="border-b-[6px] border-double border-cv-ink-950 px-8 xl:px-12 pt-10 pb-7">
				<div
					class="flex items-baseline justify-between font-['Public_Sans'] text-[10px] font-semibold tracking-[0.2em] text-cv-ink-800 uppercase"
				>
					<span>Document SUDO-CR / {app.result?.case_id ?? app.selectedCase ?? '—'}</span>
					<span>Issued {today}</span>
					<a href="/v" class="underline decoration-1 underline-offset-2">All variants</a>
				</div>
				<div class="mt-8 flex items-end justify-between gap-8">
					<h1
						class="text-[88px] leading-[0.8] font-semibold tracking-[-0.03em] text-cv-ink-950 italic"
					>
						sudo
					</h1>
					<p class="max-w-md pb-1 text-right text-xl leading-snug text-cv-ink-800">
						Compliance requirements report
						<span class="block font-['Public_Sans'] text-[11px] tracking-[0.14em] uppercase opacity-80">
							prepared in collaboration with Certivity
						</span>
					</p>
				</div>
			</header>

			<section class="border-b border-black/20 px-8 xl:px-12 py-7">
				<h2 class="mb-4 flex items-baseline gap-3 text-lg font-semibold">
					<span class="font-['Public_Sans'] text-xs text-cv-teal-700">§1</span> Particulars of submission
				</h2>
				<form
					class="grid grid-cols-[1fr_200px] gap-x-8 gap-y-4"
					onsubmit={(e) => {
						e.preventDefault();
						app.submit();
					}}
				>
					<div class="grid grid-cols-[110px_1fr] items-baseline gap-x-4 gap-y-3">
						<span class="label">Case</span>
						<Select.Root
							type="single"
							value={app.selectedCase}
							onValueChange={(v) => app.loadCase(v)}
							items={app.cases.map((c) => ({ value: c, label: c }))}
						>
							<Select.Trigger
								class="flex w-72 items-center justify-between border-b border-black pb-0.5 text-left"
							>
								{app.selectedCase || 'Select case'}
								<span aria-hidden="true" class="font-['Public_Sans'] text-xs">▾</span>
							</Select.Trigger>
							<Select.Portal>
								<Select.Content
									sideOffset={4}
									class="z-50 max-h-64 w-(--bits-select-anchor-width) overflow-auto border border-black bg-white font-['Source_Serif_4'] text-[15px]"
								>
									<Select.Viewport>
										{#each app.cases as c (c)}
											<Select.Item
												value={c}
												label={c}
												class="cursor-default px-3 py-1 data-highlighted:bg-cv-mint-50 data-selected:font-semibold"
											>
												{c}
											</Select.Item>
										{/each}
									</Select.Viewport>
								</Select.Content>
							</Select.Portal>
						</Select.Root>

						<span class="label">Spec file</span>
						<input
							type="file"
							accept=".md,.txt,text/*"
							onchange={(e) => app.setSpecFile(e.currentTarget.files?.[0])}
							class="file-input"
						/>

						<span class="label self-start pt-1">Product spec</span>
						<textarea
							bind:value={app.spec}
							rows="7"
							class="w-full resize-y border border-black/40 bg-cv-mint-50/50 p-3 font-['Source_Serif_4'] text-[13px] leading-relaxed"
						></textarea>
					</div>

					<div class="flex flex-col gap-2">
						<span class="label">Exhibit A — exploded view</span>
						<div class="flex h-36 items-center justify-center border border-black/40 p-2">
							{#if app.imageUrl}
								<img src={app.imageUrl} alt="Exploded view" class="max-h-full max-w-full object-contain" />
							{:else}
								<span class="text-sm italic opacity-50">Not supplied</span>
							{/if}
						</div>
						<input
							type="file"
							accept="image/*"
							onchange={(e) => app.setImageFile(e.currentTarget.files?.[0])}
							class="file-input"
						/>
						<div class="mt-auto flex flex-col gap-2 pt-2">
							<button
								disabled={app.loading}
								class="border border-cv-ink-950 bg-cv-ink-950 py-2 font-['Public_Sans'] text-xs font-semibold tracking-[0.16em] text-white uppercase hover:bg-cv-teal-700 disabled:opacity-60"
							>
								{app.loading ? 'Compiling report…' : 'Run assessment'}
							</button>
							<button
								type="button"
								disabled={!app.result}
								onclick={() => app.download()}
								class="border border-cv-ink-950 py-2 font-['Public_Sans'] text-xs font-semibold tracking-[0.16em] text-cv-ink-950 uppercase hover:bg-cv-mint-50 disabled:opacity-40"
							>
								Download JSON
							</button>
						</div>
					</div>
				</form>
				{#if app.error}
					<p class="mt-4 border-l-4 border-red-700 py-1 pl-3 text-sm text-red-800">
						<span class="font-['Public_Sans'] text-[10px] font-bold tracking-[0.16em] uppercase">Error</span>
						{app.error}
					</p>
				{/if}
			</section>

			<section class="border-b border-black/20 px-8 xl:px-12 py-7">
				<h2 class="mb-4 flex items-baseline gap-3 text-lg font-semibold">
					<span class="font-['Public_Sans'] text-xs text-cv-teal-700">§2</span> Executive summary
				</h2>
				{#if app.byRegulation.length}
					<p class="mb-4 max-w-2xl leading-relaxed">
						The submitted product is subject to <strong>{total}</strong> requirements drawn from
						<strong>{app.byRegulation.length}</strong> UN Regulations. Each finding in §3 cites the
						paragraph and page of the regulation text it derives from;
						<strong>{reviewed.size}</strong> of {total} have been marked as reviewed.
					</p>
					<table class="w-full border-collapse text-left text-sm">
						<thead>
							<tr class="border-y-2 border-black font-['Public_Sans'] text-[10px] tracking-[0.14em] uppercase">
								<th class="py-1.5 pr-4 font-semibold">Regulation</th>
								<th class="py-1.5 pr-4 font-semibold">Title</th>
								<th class="py-1.5 pr-4 font-semibold">Pages cited</th>
								<th class="py-1.5 pr-4 text-right font-semibold">Reviewed</th>
								<th class="py-1.5 text-right font-semibold">Requirements</th>
							</tr>
						</thead>
						<tbody>
							{#each app.byRegulation as g (g.regulation)}
								<tr class="border-b border-black/15 align-baseline">
									<td class="py-1.5 pr-4 font-semibold whitespace-nowrap">{g.regulation}</td>
									<td class="py-1.5 pr-4">{g.title}</td>
									<td class="py-1.5 pr-4 tabular-nums">{pagesCited(g.requirements)}</td>
									<td class="py-1.5 pr-4 text-right tabular-nums">
										{g.requirements.filter((r) => reviewed.has(r.id)).length}
									</td>
									<td class="py-1.5 text-right font-semibold tabular-nums">{g.count}</td>
								</tr>
							{/each}
							<tr class="border-b-2 border-black">
								<td colspan="3" class="py-1.5 font-['Public_Sans'] text-[10px] font-semibold tracking-[0.14em] uppercase">Total</td>
								<td class="py-1.5 pr-4 text-right tabular-nums">{reviewed.size}</td>
								<td class="py-1.5 text-right font-semibold tabular-nums">{total}</td>
							</tr>
						</tbody>
					</table>
				{:else}
					<p class="italic opacity-60">{app.loading ? 'Assessment in progress…' : 'No assessment on file.'}</p>
				{/if}
			</section>

			<section class="px-8 xl:px-12 pt-7 pb-12">
				<h2 class="mb-1 flex items-baseline gap-3 text-lg font-semibold">
					<span class="font-['Public_Sans'] text-xs text-cv-teal-700">§3</span> Findings
				</h2>
				<p class="mb-6 text-sm italic opacity-70">
					Select a finding to open its source page in the annex. Tick the box once verified.
				</p>

				{#each app.byRegulation as g, gi (g.regulation)}
					<h3
						class="mt-6 mb-0 grid gap-8 xl:grid-cols-[1fr_180px] border-b-2 border-black pb-1 first-of-type:mt-0"
					>
						<span class="font-semibold">3.{gi + 1}&ensp;{g.regulation} — {g.title}</span>
						<span class="hidden self-end font-['Public_Sans'] text-[10px] font-semibold tracking-[0.14em] text-cv-ink-800 uppercase xl:block">
							Citation
						</span>
					</h3>
					<ol>
						{#each g.requirements as req, ri (req.id)}
							{@const url = app.pdfUrl(req.source)}
							{@const done = reviewed.has(req.id)}
							{@const active = app.selectedId === req.id}
							<li
								class="grid grid-cols-[28px_44px_minmax(0,1fr)_84px] items-start gap-x-3 xl:grid-cols-[28px_52px_1fr_92px_180px] border-b border-black/15 py-3 {active
									? 'bg-cv-mint-50 shadow-[inset_3px_0_0_var(--color-cv-teal-700)]'
									: ''}"
							>
								<Checkbox.Root
									checked={done}
									onCheckedChange={(v) => toggle(req.id, v)}
									aria-label="Mark {req.id} reviewed"
									class="mt-1 ml-1 flex size-4 items-center justify-center border border-black bg-white data-[state=checked]:bg-cv-ink-950"
								>
									{#snippet children({ checked })}
										{#if checked}
											<svg viewBox="0 0 12 12" class="size-3 text-white" aria-hidden="true">
												<path d="M2 6.5 5 9l5-6" fill="none" stroke="currentColor" stroke-width="1.8" />
											</svg>
										{/if}
									{/snippet}
								</Checkbox.Root>
								<span class="pt-0.5 font-['Public_Sans'] text-xs font-semibold tabular-nums">
									3.{gi + 1}.{ri + 1}
								</span>
								<button
									type="button"
									onclick={() => app.select(req.id)}
									class="cursor-pointer text-left leading-relaxed hover:underline hover:decoration-cv-teal-500 hover:decoration-1 hover:underline-offset-4"
								>
									{req.text}
								</button>
								<span class="pt-0.5">
									<span class="stamp {done ? 'stamp-done' : ''}">{done ? 'Verified' : 'Open'}</span>
								</span>
								<aside class="col-span-2 col-start-3 mt-2 border-l border-cv-teal-700/60 pl-3 text-[13px] leading-snug text-cv-ink-800 xl:col-span-1 xl:col-start-auto xl:mt-0">
									<span class="block font-['Public_Sans'] text-[10px] font-semibold tracking-[0.1em]">{req.id}</span>
									<span class="block italic">{req.source.regulation}, rev. {req.source.version}</span>
									{#if req.source.paragraph}<span class="block">¶ {req.source.paragraph}</span>{/if}
									{#if url}
										<a
											href={url}
											target="_blank"
											rel="noreferrer"
											class="font-semibold text-cv-teal-700 underline decoration-1 underline-offset-2">p. {req.source.page} ↗</a
										>
									{:else}
										<span>p. {req.source.page}</span>
									{/if}
								</aside>
							</li>
						{/each}
					</ol>
				{/each}

				{#if app.byRegulation.length}
					<p class="mt-10 border-t border-black pt-2 font-['Public_Sans'] text-[10px] tracking-[0.14em] uppercase opacity-70">
						End of findings — sudo · in collaboration with Certivity
					</p>
				{/if}
			</section>
		</article>
	</main>

	<aside class="flex w-[32%] max-w-[560px] min-w-[300px] flex-col border-l border-black/30 bg-white">
		<div class="border-b-2 border-black px-5 pt-5 pb-3">
			<div class="font-['Public_Sans'] text-[10px] font-semibold tracking-[0.2em] text-cv-teal-700 uppercase">
				Annex — source page
			</div>
			{#if app.selected}
				<p class="mt-1 leading-snug">
					<span class="font-semibold">{app.selected.source.regulation}</span>
					<span class="italic">rev. {app.selected.source.version}</span>
					{#if app.selected.source.paragraph}· ¶ {app.selected.source.paragraph}{/if}
					· p. {app.selected.source.page}
				</p>
				<p class="mt-1 font-['Public_Sans'] text-[11px] opacity-70">Finding {app.selected.id}</p>
			{/if}
		</div>
		{#if app.selected && selectedUrl}
			{#key selectedUrl}
				<iframe src={selectedUrl} title="Source page" class="min-h-0 flex-1 border-0"></iframe>
			{/key}
		{:else}
			<p class="p-5 italic opacity-60">No finding selected.</p>
		{/if}
	</aside>
</div>

<style>
	.label {
		font-family: 'Public Sans', sans-serif;
		font-size: 10px;
		font-weight: 600;
		letter-spacing: 0.14em;
		text-transform: uppercase;
		color: var(--color-cv-ink-800);
	}
	.file-input {
		font-family: 'Public Sans', sans-serif;
		font-size: 12px;
	}
	.file-input::file-selector-button {
		margin-right: 0.5rem;
		border: 1px solid black;
		background: white;
		padding: 0.15rem 0.6rem;
		font: inherit;
	}
	.stamp {
		display: inline-block;
		transform: rotate(-3deg);
		border: 1.5px solid var(--color-cv-teal-700);
		outline: 1px solid var(--color-cv-teal-700);
		outline-offset: 1.5px;
		padding: 0 0.4rem;
		font-family: 'Public Sans', sans-serif;
		font-size: 9.5px;
		font-weight: 700;
		letter-spacing: 0.18em;
		text-transform: uppercase;
		color: var(--color-cv-teal-700);
		opacity: 0.55;
	}
	.stamp-done {
		opacity: 1;
		background: var(--color-cv-mint-50);
	}
</style>
