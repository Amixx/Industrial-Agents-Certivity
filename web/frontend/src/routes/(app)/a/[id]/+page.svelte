<script lang="ts">
import { Dialog } from 'bits-ui';
import { tick } from 'svelte';
import { api } from '#lib/api/client.ts';
import { pdfUrl } from '#lib/api/regulations.ts';
import { downloadSubmission } from '#lib/api/submission.ts';
import type { Assessment, RegulationUpdate } from '#lib/api/types.ts';
import AssessmentHeader from '#lib/components/AssessmentHeader.svelte';
import Markdown from '#lib/components/Markdown.svelte';
import SourceViewer from '#lib/components/SourceViewer.svelte';
import Citation from '#lib/ui/Citation.svelte';
import { page } from '$app/state';

let assessment = $state<Assessment | null>(null);
let loaded = $state(false);
let updates: RegulationUpdate[] = $state([]);
let selectedId: string | null = $state(null);
let query = $state('');
let regulationFilter: string | null = $state(null);
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

const filtered = $derived.by(() => {
	const q = query.trim().toLowerCase();
	return (assessment?.requirements ?? []).filter(
		(r) =>
			(!regulationFilter || r.source.regulation === regulationFilter) &&
			(!q ||
				r.text.toLowerCase().includes(q) ||
				r.id.toLowerCase().includes(q) ||
				r.source.paragraph.includes(q)),
	);
});

const groups = $derived(
	included
		.map((reg) => ({
			...reg,
			requirements: filtered.filter((r) => r.source.regulation === reg.regulation),
		}))
		.filter((g) => g.requirements.length),
);
const ordered = $derived(groups.flatMap((g) => g.requirements));
const selected = $derived(assessment?.requirements.find((r) => r.id === selectedId) ?? null);
const selectedUrl = $derived(selected ? pdfUrl(selected.source) : null);

const pending = $derived(updates.filter((u) => !u.applied));
const affected = $derived(
	pending.reduce(
		(n, u) => n + u.changes.filter((c) => c.change !== 'added' || c.relevant).length,
		0,
	),
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
	const step =
		e.key === 'j' || e.key === 'ArrowDown' ? 1 : e.key === 'k' || e.key === 'ArrowUp' ? -1 : 0;
	if (!step || !ordered.length) return;
	e.preventDefault();
	const i = ordered.findIndex((r) => r.id === selectedId);
	const next = ordered[Math.min(ordered.length - 1, Math.max(0, i + step))];
	select(next.id);
}
</script>

<svelte:window onkeydown={onKeydown} />
<svelte:head><title>{assessment?.caseName ?? 'Assessment'} | sudo</title></svelte:head>

{#if assessment}
	<AssessmentHeader {assessment}>
		{#if pending.length}
			<a href="/a/{assessment.id}/updates" class="ui-btn justify-start">
				<span class="size-2.5 shrink-0 bg-cv-mint-300 outline outline-1 outline-black"></span>
				<span>{pending.length} regulation{pending.length === 1 ? '' : 's'} updated</span>
				<span class="font-normal">{affected} requirements affected</span>
			</a>
		{:else if updates.length}
			<span class="text-xs">Up to date</span>
			<a href="/a/{assessment.id}/updates" class="ui-link text-xs">Update log</a>
		{/if}
		<button type="button" class="ui-btn" onclick={() => (specOpen = true)}>Spec</button>
		<button
			type="button"
			class="ui-btn"
			onclick={() => assessment && downloadSubmission(assessment)}
		>
			Download JSON
		</button>
	</AssessmentHeader>

	<Dialog.Root bind:open={specOpen}>
		<Dialog.Portal>
			<Dialog.Overlay class="fixed inset-0 z-40 bg-black/30" />
			<Dialog.Content
				class="ui-app fixed top-1/2 left-1/2 z-50 flex max-h-[85vh] min-h-0 w-[min(52rem,92vw)] -translate-x-1/2 -translate-y-1/2 flex-col rounded-control border-2 border-black bg-white"
			>
				<header class="flex items-end justify-between border-b-2 border-black px-6 pt-4 pb-3">
					<Dialog.Title class="text-sm font-bold">
						Spec <span class="ml-2 font-normal">{assessment.caseName ?? ''}</span>
					</Dialog.Title>
					<Dialog.Close class="ui-link cursor-pointer text-xs">Close</Dialog.Close>
				</header>
				<Dialog.Description class="sr-only"
					>The product spec this assessment was run on.</Dialog.Description
				>
				<div class="min-h-0 flex-1 overflow-auto px-6 py-5">
					<Markdown source={assessment.spec} />
				</div>
			</Dialog.Content>
		</Dialog.Portal>
	</Dialog.Root>

	<div class="ui-grid min-h-0 flex-1">
		<main class="col-span-4 flex min-h-0 flex-col">
			<header class="flex items-end justify-between pt-4 pb-3">
				<h2 class="text-sm font-bold">Requirements</h2>
				<div class="text-right">
					<span class="ui-count text-4xl">{ordered.length}</span>
					<span class="ml-1 text-xs tabular-nums">of {assessment.requirements.length}</span>
				</div>
			</header>
			<input
				type="search"
				bind:value={query}
				placeholder="Search requirements, ids, §"
				class="ui-input w-full"
			>
			<div class="flex flex-wrap gap-1 pt-2 pb-2">
				<button
					type="button"
					class="ui-toggle {regulationFilter === null ? 'ui-toggle-on' : ''}"
					onclick={() => (regulationFilter = null)}
				>
					All
				</button>
				{#each included as reg (reg.regulation)}
					<button
						type="button"
						class="ui-toggle {regulationFilter === reg.regulation ? 'ui-toggle-on' : ''}"
						title={reg.title}
						onclick={() => (regulationFilter = reg.regulation)}
					>
						{reg.regulation.replace('UN ', '')}
						<span class="ml-1 font-normal tabular-nums">{reg.requirementCount}</span>
					</button>
				{/each}
			</div>

			<div class="min-h-0 flex-1 overflow-auto">
				{#each groups as g (g.regulation)}
					<section>
						<h3
							class="sticky top-0 z-10 flex justify-between gap-3 border-b-2 border-black bg-white pt-4 pb-1 pl-5 text-sm"
						>
							<span class="truncate"
								><span class="font-bold">{g.regulation}</span>
								<span class="ml-1 font-medium">{g.title}</span></span
							>
							<span class="tabular-nums">{g.requirements.length}</span>
						</h3>
						<ul>
							{#each g.requirements as req (req.id)}
								{@const active = selectedId === req.id}
								<li id="req-{req.id}">
									<button
										type="button"
										class="group ui-rule-soft grid w-full cursor-pointer grid-cols-[4.5rem_1fr] border-b py-2.5 pl-5 text-left outline-none hover:bg-black/[0.03] focus-visible:bg-cv-mint-50 {active
											? 'ui-row-selected bg-cv-mint-50'
											: ''}"
										style:--ui-marker-top="0.95rem"
										onclick={() => select(req.id)}
									>
										<span
											class="pr-2 text-base leading-tight font-light break-all text-cv-teal-700 tabular-nums"
											>{req.source.paragraph}</span
										>
										<span class="text-sm leading-snug {active ? 'font-medium' : 'line-clamp-3'}"
											>{req.text}</span
										>
									</button>
								</li>
							{/each}
						</ul>
					</section>
				{:else}
					<p class="py-4 pl-5">No requirements match.</p>
				{/each}
			</div>
			<div class="ui-rule-soft border-t py-1.5 text-xs">j / k or ↑ / ↓ to move</div>
		</main>

		<aside class="col-span-8 flex min-h-0 flex-col pb-4">
			{#if selected}
				<header class="flex items-end justify-between gap-6 pt-4 pb-3">
					<div class="min-w-0">
						<div class="flex flex-wrap items-baseline gap-x-4 text-xs">
							<span class="font-bold">{selected.id}</span>
							<Citation source={selected.source} />
						</div>
						<p class="mt-1 line-clamp-2 text-base leading-snug font-medium">{selected.text}</p>
					</div>
					<div class="shrink-0 text-right">
						<div class="ui-count text-5xl">§{selected.source.paragraph}</div>
						<div class="mt-1 text-xs tabular-nums">page {selected.source.page}</div>
					</div>
				</header>
				{#if selectedUrl}
					<SourceViewer
						url={selectedUrl}
						page={selected.source.page}
						highlight={{ paragraph: selected.source.paragraph, text: selected.text }}
						label={selected.id}
						class="min-h-0 w-full flex-1 border-t-2 border-black"
					/>
				{:else}
					<p class="py-4 text-sm">
						No PDF for {selected.source.regulation} {selected.source.version}.
					</p>
				{/if}
			{:else}
				<p class="max-w-[22ch] pt-6 text-3xl leading-tight font-light">
					Select a requirement to show its source page here.
				</p>
			{/if}
		</aside>
	</div>
{:else if loaded}
	<p class="ui-section">Assessment not found. <a href="/history" class="ui-link">See history</a></p>
{/if}
