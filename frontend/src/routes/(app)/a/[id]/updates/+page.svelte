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
import { page } from '$app/state';

let assessment = $state<Assessment | null>(null);
let updates: RegulationUpdate[] | null = $state(null);
let applying: string | null = $state(null);

$effect(() => {
	const id = page.params.id!;
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
	modified: 'border-cv-teal-700 text-cv-teal-700',
	removed: 'border-cv-ink-800 bg-cv-ink-800 text-cv-mint-50',
	added: 'border-cv-teal-700 bg-cv-mint-300',
};
</script>

<svelte:head><title>Updates · sudo</title></svelte:head>

{#if assessment}
	<AssessmentHeader {assessment}>
		<a href="/a/{assessment.id}" class="ui-btn">← Requirements</a>
	</AssessmentHeader>
{/if}

{#snippet row(
	c: RequirementChange,
	u: RegulationUpdate,
	latest: string | null,
)}
	<li
		class="ui-rule-soft grid grid-cols-[6rem_6rem_1fr_16rem] gap-4 border-b px-4 py-3 last:border-b-0 {c.change ===
			'added' && !c.relevant
			? 'opacity-60'
			: ''}"
	>
		<span><span class="ui-tag {kindStyle[c.change]}">{c.change}</span></span>
		<span class="ui-mono text-xs">{c.requirementId ?? 'new'}</span>
		<div class="text-sm">
			{#if c.change === 'modified'}
				<WordDiff before={c.oldText} after={c.newText} />
			{:else if c.change === 'removed'}
				<p class="leading-relaxed line-through opacity-60">{c.oldText}</p>
			{:else}
				<p class="leading-relaxed"><ins class="bg-cv-mint-300 no-underline">{c.newText}</ins></p>
			{/if}
			{#if c.relevanceNote}
				<p class="mt-1 text-xs opacity-70">{c.relevanceNote}</p>
			{/if}
		</div>
		<div class="space-y-1 text-xs">
			<p class="leading-snug">{c.reason}</p>
			<p class="ui-mono text-[11px] opacity-70">
				{#if latest}
					<a href="{latest}#page={c.source.page}" target="_blank" rel="noreferrer" class="ui-link">
						{u.toVersion}
						· p. {c.source.page} · § {c.source.paragraph}
					</a>
				{:else}
					{u.toVersion}
					· p. {c.source.page} · § {c.source.paragraph}
				{/if}
			</p>
		</div>
	</li>
{/snippet}

<div class="min-h-0 flex-1 overflow-auto">
	{#if updates === null}
		<p class="p-4 opacity-60">Checking for regulation updates…</p>
	{:else if !updates.length}
		<p class="p-4 opacity-60">All cited regulations are at their latest version.</p>
	{:else}
		{#each updates as u (u.regulation)}
			{@const latest = pdfUrl({ regulation: u.regulation, version: u.toVersion })}
			{@const relevant = u.changes.filter(isShown)}
			{@const rest = u.changes.filter((c) => !isShown(c))}
			{@const touched = u.changes.filter((c) => c.change !== 'added').length}
			{@const added = u.changes.filter((c) => c.change === 'added' && c.relevant).length}
			<section class="ui-rule border-b">
				<header
					class="ui-rule-soft flex items-center justify-between gap-4 border-b bg-cv-mint-300/30 px-4 py-2"
				>
					<div class="flex flex-wrap items-baseline gap-x-3">
						<span class="ui-mono text-base font-medium">{u.regulation}</span>
						<span class="ui-mono text-xs">{u.fromVersion} → {u.toVersion}</span>
						{#if u.stats}
							<span class="text-xs opacity-70">
								{u.stats.changed}
								paragraphs changed, {u.stats.added} added, {u.stats.removed} removed
							</span>
						{/if}
					</div>
					{#if u.applied}
						<span class="ui-tag border-cv-teal-700 text-cv-teal-700">Applied</span>
					{:else}
						<button
							class="ui-btn ui-btn-primary"
							disabled={applying !== null}
							onclick={() => apply(u.regulation)}
						>
							{applying === u.regulation ? 'Applying…' : 'Apply update'}
						</button>
					{/if}
				</header>
				<p class="ui-rule-soft border-b px-4 py-2 text-sm">
					{#if touched === 0}
						None of this assessment's {cited(u.regulation)} cited {u.regulation} paragraphs changed.
					{:else}
						{touched}
						of this assessment's {cited(u.regulation)} cited {u.regulation} paragraphs changed.
					{/if}
					{#if added}
						<strong>{added} new obligation{added === 1 ? '' : 's'} may apply.</strong>
					{:else}
						No new obligations appear relevant to this product.
					{/if}
				</p>
				<ol>
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
						class="ui-link px-4 py-2 text-xs"
						onclick={() => (showIrrelevant[u.regulation] = !showIrrelevant[u.regulation])}
					>
						{showIrrelevant[u.regulation] ? 'Hide' : 'Show'} {rest.length} not relevant to this
						product
					</button>
				{/if}
			</section>
		{/each}
	{/if}
</div>
