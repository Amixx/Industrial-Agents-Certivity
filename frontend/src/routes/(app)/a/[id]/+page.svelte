<script lang="ts">
	import { tick } from 'svelte';
	import { Collapsible, Dialog } from 'bits-ui';
	import { page } from '$app/state';
	import { api } from '#lib/api/client.ts';
	import { pdfUrl } from '#lib/api/regulations.ts';
	import { downloadSubmission } from '#lib/api/submission.ts';
	import type { Assessment, RegulationUpdate } from '#lib/api/types.ts';
	import AssessmentHeader from '#lib/components/AssessmentHeader.svelte';
	import Markdown from '#lib/components/Markdown.svelte';
	import SourceViewer from '#lib/components/SourceViewer.svelte';
	import Citation from '#lib/ui/Citation.svelte';
	import Panel from '#lib/ui/Panel.svelte';

	let assessment = $state<Assessment | null>(null);
	let loaded = $state(false);
	let updates: RegulationUpdate[] = $state([]);
	let selectedId: string | null = $state(null);
	let query = $state('');
	let regulationFilter: string | null = $state(null);
	let excludedOpen = $state(false);
	let specOpen = $state(false);

	$effect(() => {
		const id = page.params.id!;
		loaded = false;
		api.getAssessment(id).then((a) => {
			assessment = a;
			loaded = true;
			selectedId = a?.requirements[0]?.id ?? null;
		});
		api.checkUpdates(id).then((u) => (updates = u));
	});

	const included = $derived(assessment?.regulations.filter((r) => r.included) ?? []);
	const excluded = $derived(assessment?.regulations.filter((r) => !r.included) ?? []);

	const filtered = $derived.by(() => {
		const q = query.trim().toLowerCase();
		return (assessment?.requirements ?? []).filter(
			(r) =>
				(!regulationFilter || r.source.regulation === regulationFilter) &&
				(!q ||
					r.text.toLowerCase().includes(q) ||
					r.id.toLowerCase().includes(q) ||
					r.source.paragraph.includes(q))
		);
	});

	const groups = $derived(
		included
			.map((reg) => ({
				...reg,
				requirements: filtered.filter((r) => r.source.regulation === reg.regulation)
			}))
			.filter((g) => g.requirements.length)
	);
	const ordered = $derived(groups.flatMap((g) => g.requirements));
	const selected = $derived(assessment?.requirements.find((r) => r.id === selectedId) ?? null);
	const selectedUrl = $derived(selected ? pdfUrl(selected.source) : null);

	const pending = $derived(updates.filter((u) => !u.applied));
	const affected = $derived(
		pending.reduce((n, u) => n + u.changes.filter((c) => c.change !== 'added' || c.relevant).length, 0)
	);

	async function select(id: string) {
		selectedId = id;
		await tick();
		const row = document.querySelector<HTMLButtonElement>(`#req-${id} button`);
		row?.focus({ preventScroll: true });
		row?.scrollIntoView({ block: 'nearest' });
	}

	function onKeydown(e: KeyboardEvent) {
		const target = e.target as HTMLElement;
		if (target.matches('input, textarea, [contenteditable]') || e.metaKey || e.ctrlKey) return;
		const step = e.key === 'j' || e.key === 'ArrowDown' ? 1 : e.key === 'k' || e.key === 'ArrowUp' ? -1 : 0;
		if (!step || !ordered.length) return;
		e.preventDefault();
		const i = ordered.findIndex((r) => r.id === selectedId);
		const next = ordered[Math.min(ordered.length - 1, Math.max(0, i + step))];
		select(next.id);
	}
</script>

<svelte:window onkeydown={onKeydown} />
<svelte:head><title>{assessment?.caseName ?? 'Assessment'} · sudo</title></svelte:head>

{#if assessment}
	<AssessmentHeader {assessment}>
		{#if pending.length}
			<a href="/a/{assessment.id}/updates" class="ui-btn border-cv-teal-700 bg-cv-mint-300 normal-case tracking-normal">
				<span class="ui-mono font-medium">●</span>
				{pending.length} regulation{pending.length === 1 ? '' : 's'} updated · {affected} requirements affected
			</a>
		{:else if updates.length}
			<a href="/a/{assessment.id}/updates" class="ui-link text-xs">Up to date · update log</a>
		{/if}
		<button class="ui-btn" onclick={() => (specOpen = true)}>Spec</button>
		<button class="ui-btn" onclick={() => assessment && downloadSubmission(assessment)}>Download JSON</button>
	</AssessmentHeader>

	<Dialog.Root bind:open={specOpen}>
		<Dialog.Portal>
			<Dialog.Overlay class="fixed inset-0 z-40 bg-cv-ink-800/40" />
			<Dialog.Content
				class="ui-rule fixed top-1/2 left-1/2 z-50 flex max-h-[85vh] w-[min(52rem,92vw)] -translate-x-1/2 -translate-y-1/2 flex-col border bg-white"
			>
				<header class="ui-rule flex items-baseline justify-between border-b px-4 py-2">
					<Dialog.Title class="ui-label font-medium opacity-100">
						Spec <span class="ui-mono opacity-60">{assessment.caseName ?? ''}</span>
					</Dialog.Title>
					<Dialog.Close class="ui-link text-xs">close</Dialog.Close>
				</header>
				<Dialog.Description class="sr-only">The product spec this assessment was run on.</Dialog.Description>
				<div class="min-h-0 flex-1 overflow-auto p-5">
					<Markdown source={assessment.spec} />
				</div>
			</Dialog.Content>
		</Dialog.Portal>
	</Dialog.Root>

	<div class="grid min-h-0 flex-1 grid-cols-[19rem_minmax(0,1fr)_minmax(26rem,38%)]">
		<aside class="ui-rule min-h-0 overflow-auto border-r">
			<Panel title="Profile" meta="from spec">
				<dl class="space-y-3 px-3 py-2 text-xs">
					<div>
						<dt class="ui-label">Product</dt>
						<dd>{assessment.profile.productType}</dd>
					</div>
					<div>
						<dt class="ui-label">Vehicle category</dt>
						<dd>{assessment.profile.vehicleCategory}</dd>
					</div>
					{#each [{ label: 'Parts', items: assessment.profile.parts }, { label: 'Functions', items: assessment.profile.functions }, { label: 'Materials', items: assessment.profile.materials }] as list (list.label)}
						<div>
							<dt class="ui-label">{list.label} <span class="ui-mono">{list.items.length}</span></dt>
							<dd>
								<ul>
									{#each list.items as item (item)}<li class="leading-snug">— {item}</li>{/each}
								</ul>
							</dd>
						</div>
					{/each}
				</dl>
			</Panel>

			<Panel title="Regulations" meta="{included.length} of {assessment.regulations.length} considered" class="ui-rule border-t">
				<ul>
					{#each included as reg (reg.regulation)}
						<li class="ui-rule-soft border-b">
							<button
								class="block w-full px-3 py-2 text-left text-xs hover:bg-white {regulationFilter === reg.regulation
									? 'ui-row-selected'
									: ''}"
								onclick={() => (regulationFilter = regulationFilter === reg.regulation ? null : reg.regulation)}
							>
								<div class="flex items-baseline justify-between gap-2">
									<span><span class="ui-mono font-medium">{reg.regulation}</span> <span class="ui-mono opacity-60">{reg.version}</span></span>
									<span class="ui-mono font-medium">×{reg.requirementCount}</span>
								</div>
								<div class="font-medium">{reg.title}</div>
								<p class="mt-0.5 leading-snug opacity-75">{reg.reason}</p>
							</button>
						</li>
					{/each}
				</ul>
				<Collapsible.Root bind:open={excludedOpen}>
					<Collapsible.Trigger class="flex w-full items-baseline justify-between px-3 py-2 text-left hover:bg-white">
						<span class="ui-label font-medium opacity-100">Excluded ({excluded.length})</span>
						<span class="ui-mono text-xs">{excludedOpen ? '−' : '+'}</span>
					</Collapsible.Trigger>
					<Collapsible.Content>
						<ul class="pb-2">
							{#each excluded as reg (reg.regulation)}
								<li class="ui-rule-soft border-t px-3 py-1.5 text-xs">
									<div>
										<span class="ui-mono font-medium">{reg.regulation}</span>
										<span class="opacity-70">{reg.title}</span>
									</div>
									<p class="leading-snug opacity-75">{reg.reason}</p>
								</li>
							{/each}
						</ul>
					</Collapsible.Content>
				</Collapsible.Root>
			</Panel>
		</aside>

		<main class="flex min-h-0 flex-col">
			<div class="ui-rule flex items-center gap-2 border-b px-3 py-2">
				<input
					type="search"
					bind:value={query}
					placeholder="Search requirements, ids, §"
					class="ui-input min-w-0 flex-1"
				/>
				<div class="flex">
					<button
						class="ui-tag h-7 cursor-pointer px-2 {regulationFilter === null ? 'bg-cv-ink-800 text-cv-mint-50' : 'hover:bg-white'}"
						onclick={() => (regulationFilter = null)}>All</button
					>
					{#each included as reg (reg.regulation)}
						<button
							class="ui-tag -ml-px h-7 cursor-pointer px-2 {regulationFilter === reg.regulation
								? 'bg-cv-ink-800 text-cv-mint-50'
								: 'hover:bg-white'}"
							onclick={() => (regulationFilter = reg.regulation)}>{reg.regulation.replace('UN ', '')}</button
						>
					{/each}
				</div>
				<span class="ui-mono w-16 text-right text-xs opacity-70">{ordered.length}/{assessment.requirements.length}</span>
			</div>

			<div class="min-h-0 flex-1 overflow-auto">
				{#each groups as g (g.regulation)}
					<section>
						<h3 class="ui-rule-soft sticky top-0 z-10 border-b bg-cv-mint-50 px-3 py-1 text-xs font-semibold">
							<span class="ui-mono">{g.regulation} {g.version}</span> — {g.title}
							<span class="ui-mono font-normal opacity-60">({g.requirements.length})</span>
						</h3>
						<ul>
							{#each g.requirements as req (req.id)}
								<li id="req-{req.id}">
									<button
										class="ui-rule-soft grid w-full grid-cols-[4.5rem_1fr] gap-x-3 border-b px-3 py-2 text-left hover:bg-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cv-teal-400 {selectedId ===
										req.id
											? 'ui-row-selected'
											: ''}"
										onclick={() => select(req.id)}
									>
										<span class="ui-mono text-xs">{req.id}</span>
										<span>
											<span class="block leading-snug">{req.text}</span>
											<Citation source={req.source} showRegulation={false} />
										</span>
									</button>
								</li>
							{/each}
						</ul>
					</section>
				{:else}
					<p class="p-4 opacity-60">No requirements match.</p>
				{/each}
			</div>
			<div class="ui-rule ui-mono border-t px-3 py-1 text-[10px] opacity-60">j / k or ↑ / ↓ to move</div>
		</main>

		<aside class="ui-rule ui-surface flex min-h-0 flex-col border-l">
			{#if selected}
				<div class="ui-rule border-b px-3 py-2">
					<div class="flex items-baseline justify-between gap-2">
						<span class="ui-mono text-xs font-medium">{selected.id}</span>
						<Citation source={selected.source} />
					</div>
					<p class="mt-1 text-xs leading-snug">{selected.text}</p>
				</div>
				{#if selectedUrl}
					<SourceViewer
						url={selectedUrl}
						page={selected.source.page}
						highlight={{ paragraph: selected.source.paragraph, text: selected.text }}
						class="min-h-0 w-full flex-1"
					/>
				{:else}
					<p class="p-4 opacity-60">No PDF for {selected.source.regulation} {selected.source.version}.</p>
				{/if}
			{:else}
				<p class="p-4 opacity-60">Select a requirement to view its source page.</p>
			{/if}
		</aside>
	</div>
{:else if loaded}
	<p class="p-4">Assessment not found. <a href="/history" class="ui-link">See history</a></p>
{/if}
