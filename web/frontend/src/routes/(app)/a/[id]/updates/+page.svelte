<script lang="ts">
import { api } from '#lib/api/client.ts';
import { pdfUrl } from '#lib/api/regulations.ts';
import type {
	Assessment,
	ChangeKind,
	RegulationUpdate,
	RequirementChange,
} from '#lib/api/types.ts';
import AssessmentHeader from '#lib/components/AssessmentHeader.svelte';
import WordDiff from '#lib/ui/WordDiff.svelte';
import type { PageProps } from './$types';

let { params }: PageProps = $props();

let assessment = $state<Assessment | null>(null);
let updates: RegulationUpdate[] | null = $state(null);
let applying: string | null = $state(null);

$effect(() => {
	const id = params.id;
	api.getAssessment(id).then((a) => (assessment = a));
	api.checkUpdates(id).then((u) => (updates = u));
});

async function apply(regulation: string) {
	if (!assessment) return;
	applying = regulation;
	try {
		assessment = await api.applyUpdate(assessment.id, regulation);
		updates = await api.checkUpdates(assessment.id);
	} finally {
		applying = null;
	}
}

let showIrrelevant = $state<Record<string, boolean>>({});

const isShown = (c: RequirementChange) => c.change !== 'added' || c.relevant;

function cited(regulation: string) {
	const paragraphs = new Set(
		assessment?.requirements
			.filter((r) => r.source.regulation === regulation && !r.id.startsWith('U-'))
			.map((r) => r.source.paragraph),
	);
	return paragraphs.size;
}

const kindStyle: Record<ChangeKind, string> = {
	modified: 'bg-canvas',
	removed: 'bg-fg text-canvas',
	added: 'bg-mark text-cv-ink-950',
};
</script>

<svelte:head><title>Updates | sudo</title></svelte:head>

{#if assessment}
	<AssessmentHeader {assessment}>
		<a href="/a/{assessment.id}" class="ui-btn">Back to requirements</a>
	</AssessmentHeader>
{/if}

{#snippet row(c: RequirementChange, u: RegulationUpdate, latest: string | null)}
	<li
		class="ui-rule-soft grid grid-cols-10 gap-x-4 border-b py-4 xl:gap-x-6 {c.change === 'added' &&
		!c.relevant
			? 'opacity-50'
			: ''}"
	>
		<span class="col-span-1"><span class="ui-tag {kindStyle[c.change]}">{c.change}</span></span>
		<span class="col-span-1 text-xs font-bold">{c.requirementId ?? 'New'}</span>
		<div class="col-span-5 text-sm">
			{#if c.change === 'modified'}
				<WordDiff before={c.oldText} after={c.newText} />
			{:else if c.change === 'removed'}
				<p class="leading-relaxed text-muted line-through decoration-1">{c.oldText}</p>
			{:else}
				<p class="leading-relaxed"><ins class="bg-mark no-underline">{c.newText}</ins></p>
			{/if}
			{#if c.relevanceNote}
				<p class="mt-1 text-xs">{c.relevanceNote}</p>
			{/if}
		</div>
		<div class="col-span-3 space-y-2 text-xs">
			<p class="leading-snug">{c.reason}</p>
			<p class="flex flex-wrap gap-x-4 tabular-nums">
				{#if latest}
					<a href="{latest}#page={c.source.page}" target="_blank" rel="noreferrer" class="ui-link"
						>{u.toVersion}, page {c.source.page} ↗</a
					>
				{:else}
					<span>{u.toVersion}, page {c.source.page}</span>
				{/if}
				<span>§ {c.source.paragraph}</span>
			</p>
		</div>
	</li>
{/snippet}

<div class="min-h-0 flex-1 overflow-auto pb-10">
	{#if updates === null}
		<p class="ui-section">Checking for regulation updates…</p>
	{:else if !updates.length}
		<p class="ui-section">All cited regulations are at their latest version.</p>
	{:else}
		{#each updates as u, n (u.regulation)}
			{@const latest = pdfUrl({ regulation: u.regulation, version: u.toVersion })}
			{@const relevant = u.changes.filter(isShown)}
			{@const rest = u.changes.filter((c) => !isShown(c))}
			{@const touched = u.changes.filter((c) => c.change !== 'added').length}
			{@const added = u.changes.filter((c) => c.change === 'added' && c.relevant).length}
			<section class="ui-grid ui-section mb-12">
				<div class="col-span-2">
					<div class="ui-numeral">{n + 1}</div>
					<div class="mt-2 text-sm font-bold">{u.regulation}</div>
					<div class="text-xs tabular-nums">From {u.fromVersion}</div>
					<div class="text-xs tabular-nums">To {u.toVersion}</div>
				</div>
				<div class="col-span-10">
					<div class="grid grid-cols-10 items-start gap-x-4 xl:gap-x-6">
						<p class="col-span-5 text-xl leading-tight font-medium">
							{#if touched === 0}
								None of this assessment's {cited(u.regulation)} cited {u.regulation} paragraphs
								changed.
							{:else}
								{touched}
								of this assessment's {cited(u.regulation)} cited {u.regulation} paragraphs changed.
							{/if}
							{#if added}
								<strong class="font-bold"
									>{added}
									new obligation{added === 1 ? '' : 's'}
									may apply.</strong
								>
							{:else}
								No new obligations appear relevant to this product.
							{/if}
						</p>
						<div class="col-span-3">
							{#if u.stats}
								<div class="grid grid-cols-3 gap-x-4 xl:gap-x-6">
									{#each [
										['changed', u.stats.changed],
										['added', u.stats.added],
										['removed', u.stats.removed],
									] as const as [label, value] (label)}
										<div class="border-t-2 border-line pt-2">
											<div class="text-4xl leading-none font-light text-accent tabular-nums">
												{value}
											</div>
											<div class="mt-1 text-xs">{label}</div>
										</div>
									{/each}
								</div>
								<p class="mt-2 text-xs">Paragraphs across the whole regulation</p>
							{/if}
						</div>
						<div class="col-span-2 flex justify-end">
							{#if u.applied}
								<span class="flex items-center gap-2 text-sm font-bold">
									<span class="size-2.5 bg-mark"></span>
									Applied
								</span>
							{:else}
								<button
									type="button"
									class="ui-btn ui-btn-primary w-full"
									disabled={applying !== null}
									onclick={() => apply(u.regulation)}
								>
									{applying === u.regulation ? 'Applying…' : 'Apply update'}
								</button>
							{/if}
						</div>
					</div>
					<ol class="mt-6 border-t-2 border-line">
						{#each relevant as c, i (i)}
							{@render row(c, u, latest)}
						{/each}
						{#if showIrrelevant[u.regulation]}
							{#each rest as c, i (i)}
								{@render row(c, u, latest)}
							{/each}
						{/if}
					</ol>
					{#if rest.length}
						<button
							type="button"
							class="ui-link mt-3 cursor-pointer text-xs"
							onclick={() => (showIrrelevant[u.regulation] = !showIrrelevant[u.regulation])}
						>
							{showIrrelevant[u.regulation] ? 'Hide' : 'Show'} {rest.length} not relevant to this
							product
						</button>
					{/if}
				</div>
			</section>
		{/each}
	{/if}
</div>
