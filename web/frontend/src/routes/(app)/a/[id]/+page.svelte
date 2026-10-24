<script lang="ts">
import { Collapsible, Dialog } from 'bits-ui';
import { tick } from 'svelte';
import { api } from '#lib/api/client.ts';
import { pdfUrl } from '#lib/api/regulations.ts';
import { downloadSubmission } from '#lib/api/submission.ts';
import type { Assessment, RegulationUpdate } from '#lib/api/types.ts';
import AssessmentHeader from '#lib/components/AssessmentHeader.svelte';
import Markdown from '#lib/components/Markdown.svelte';
import SourceViewer from '#lib/components/SourceViewer.svelte';
import Citation from '#lib/ui/Citation.svelte';
import Panel from '#lib/ui/Panel.svelte';
import { page } from '$app/state';

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
		<aside class="col-span-3 min-h-0 overflow-auto pb-6">
			<Panel index={1} title="Profile" meta="From the spec">
				<dl class="space-y-4 pb-8 text-xs">
					<div>
						<dt class="ui-label">Product</dt>
						<dd class="text-sm leading-snug">{assessment.profile.productType}</dd>
					</div>
					<div>
						<dt class="ui-label">Vehicle category</dt>
						<dd class="leading-snug">{assessment.profile.vehicleCategory}</dd>
					</div>
					{#each [
						{ label: 'Parts', items: assessment.profile.parts },
						{ label: 'Functions', items: assessment.profile.functions },
						{ label: 'Materials', items: assessment.profile.materials },
					] as list (list.label)}
						<div>
							<dt class="ui-label flex justify-between border-b border-black pb-0.5">
								<span>{list.label}</span>
								<span class="tabular-nums">{list.items.length}</span>
							</dt>
							<dd>
								<ul>
									{#each list.items as item (item)}
										<li class="ui-rule-soft border-b py-1 leading-snug">{item}</li>
									{/each}
								</ul>
							</dd>
						</div>
					{/each}
				</dl>
			</Panel>

			<Panel
				index={2}
				title="Regulations"
				meta="{included.length} of {assessment.regulations.length} considered"
			>
				<ul class="border-t-2 border-black">
					{#each included as reg (reg.regulation)}
						{@const active = regulationFilter === reg.regulation}
						<li class="ui-rule-soft border-b">
							<button
								type="button"
								class="grid w-full cursor-pointer grid-cols-[1fr_auto] gap-x-3 py-3 pl-5 text-left text-xs hover:bg-black/[0.03] {active
									? 'ui-row-selected'
									: ''}"
								style:--ui-marker-top="1rem"
								onclick={() =>
									(regulationFilter = regulationFilter === reg.regulation ? null : reg.regulation)}
							>
								<div>
									<div class="text-sm">
										<span class="font-bold">{reg.regulation}</span>
										<span class="ml-1 tabular-nums">{reg.version}</span>
									</div>
									<div class="mt-0.5 font-medium">{reg.title}</div>
									<p class="mt-1 leading-snug text-black/70">{reg.reason}</p>
								</div>
								<span class="text-3xl leading-none font-light text-cv-teal-700 tabular-nums"
									>{reg.requirementCount}</span
								>
							</button>
						</li>
					{/each}
				</ul>
				<Collapsible.Root bind:open={excludedOpen}>
					<Collapsible.Trigger
						class="flex w-full cursor-pointer items-baseline justify-between rounded-control py-3 pl-5 text-left hover:bg-black/[0.03]"
					>
						<span class="text-xs font-bold">
							Excluded <span class="ml-1 font-normal tabular-nums">{excluded.length}</span>
						</span>
						<span class="pr-1 text-sm">{excludedOpen ? '−' : '+'}</span>
					</Collapsible.Trigger>
					<Collapsible.Content>
						<ul class="pb-2">
							{#each excluded as reg (reg.regulation)}
								<li class="ui-rule-soft border-t py-2 pl-5 text-xs">
									<div>
										<span class="font-bold">{reg.regulation}</span>
										<span class="ml-1">{reg.title}</span>
									</div>
									<p class="mt-0.5 leading-snug text-black/70">{reg.reason}</p>
								</li>
							{/each}
						</ul>
					</Collapsible.Content>
				</Collapsible.Root>
			</Panel>
		</aside>

		<main class="col-span-5 flex min-h-0 flex-col">
			<header class="ui-section flex items-end justify-between pb-3">
				<div>
					<div class="ui-numeral">3</div>
					<h2 class="mt-2 text-sm font-bold">Requirements</h2>
				</div>
				<div class="text-right">
					<div class="ui-count text-5xl">{ordered.length}</div>
					<div class="mt-1 text-xs tabular-nums">of {assessment.requirements.length}</div>
				</div>
			</header>
			<div class="flex items-end gap-4 pb-2">
				<input
					type="search"
					bind:value={query}
					placeholder="Search requirements, ids, §"
					class="ui-input min-w-0 flex-1"
				>
				<div class="flex gap-1">
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
							onclick={() => (regulationFilter = reg.regulation)}
						>
							{reg.regulation.replace('UN ', '')}
						</button>
					{/each}
				</div>
			</div>

			<div class="min-h-0 flex-1 overflow-auto">
				{#each groups as g (g.regulation)}
					<section>
						<h3
							class="sticky top-0 z-10 grid grid-cols-[6.5rem_1fr] border-b-2 border-black bg-white pt-5 pb-1 pl-5 text-sm"
						>
							<span class="font-bold">{g.regulation}</span>
							<span class="flex justify-between gap-3">
								<span class="truncate font-medium">{g.title}</span>
								<span class="tabular-nums">{g.requirements.length}</span>
							</span>
						</h3>
						<ul>
							{#each g.requirements as req (req.id)}
								{@const active = selectedId === req.id}
								<li id="req-{req.id}">
									<button
										type="button"
										class="group ui-rule-soft grid w-full cursor-pointer grid-cols-[6.5rem_1fr] border-b py-3 pl-5 text-left outline-none focus-visible:bg-cv-mint-50 {active
											? 'ui-row-selected'
											: ''}"
										style:--ui-marker-top="1.125rem"
										onclick={() => select(req.id)}
									>
										<span
											class="pr-2 text-xl leading-none font-light tracking-tight break-all text-cv-teal-700 tabular-nums group-hover:font-normal"
											>{req.source.paragraph}</span
										>
										<span>
											<span class="block text-[15px] leading-snug {active ? 'font-medium' : ''}"
												>{req.text}</span
											>
											<span class="mt-2 flex gap-4 text-xs">
												<span class="font-bold">{req.id}</span>
												<Citation
													source={req.source}
													showRegulation={false}
													showParagraph={false}
												/>
											</span>
										</span>
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

		<aside class="col-span-4 flex min-h-0 flex-col pb-4">
			<header
				class="ui-section flex items-end justify-between gap-4 border-b-2 border-b-black pb-2"
			>
				<div class="min-w-0">
					<div class="ui-numeral">4</div>
					<h2 class="mt-2 text-sm font-bold">Source page</h2>
					{#if selected}
						<div class="flex flex-wrap gap-x-4 text-xs">
							<span class="font-bold">{selected.id}</span>
							<Citation source={selected.source} />
						</div>
					{/if}
				</div>
				{#if selected}
					<div class="ui-numeral shrink-0">p{selected.source.page}</div>
				{/if}
			</header>
			{#if selected}
				<p class="my-3 line-clamp-4 text-sm leading-snug">{selected.text}</p>
				{#if selectedUrl}
					<SourceViewer
						url={selectedUrl}
						page={selected.source.page}
						highlight={{ paragraph: selected.source.paragraph, text: selected.text }}
						class="ui-rule min-h-0 w-full flex-1 border-t"
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
