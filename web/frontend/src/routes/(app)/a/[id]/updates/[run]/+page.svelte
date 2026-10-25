<script lang="ts">
import { cubicOut } from 'svelte/easing';
import { Tween } from 'svelte/motion';
import { api } from '#lib/api/client.ts';
import type { Assessment, ChangeKind, Hunk, RequirementChange, UpdateRun } from '#lib/api/types.ts';
import AssessmentHeader from '#lib/components/AssessmentHeader.svelte';
import PdfDrawer from '#lib/graph/PdfDrawer.svelte';
import WordDiff from '#lib/ui/WordDiff.svelte';
import HunkView from '#lib/updates/HunkView.svelte';
import {
	changeId,
	changeKinds,
	changeReading,
	hunkReading,
	paragraphName,
	type Reading,
	short,
} from '#lib/updates/run.ts';
import type { PageProps } from './$types';

let { params }: PageProps = $props();

let assessment = $state<Assessment | null>(null);
let run = $state<UpdateRun | null>(null);
let missing = $state(false);

$effect(() => {
	const { id, run: runId } = params;
	api.getAssessment(id).then((a) => (assessment = a));
	api.getUpdate(id, runId).then((r) => {
		run = r;
		missing = !r;
	});
});

let split = $state(false);
let showAll = $state(false);
let applying = $state(false);
let flash = $state<string | null>(null);
let reading = $state<{ list: Reading[]; index: number } | null>(null);

/** A hunk is relevant when a requirement cites it or it changes one. */
const relevant = (h: Hunk) => h.citedBy.length > 0 || h.changes.length > 0;
const ordered = $derived(
	run ? [...run.hunks.filter(relevant), ...run.hunks.filter((h) => !relevant(h))] : [],
);
const relevantCount = $derived(run?.hunks.filter(relevant).length ?? 0);
/** Up to this many changed paragraphs all show; past it only the relevant ones until asked. */
const SHOW_ALL_UP_TO = 40;
const all = $derived(showAll || relevantCount === 0 || ordered.length <= SHOW_ALL_UP_TO);
const shown = $derived(all ? ordered : ordered.slice(0, relevantCount));

const byKind = $derived(
	Object.fromEntries(
		changeKinds.map((k) => [k, run?.changes.filter((c) => c.change === k) ?? []]),
	) as Record<ChangeKind, RequirementChange[]>,
);

const regulationCount = $derived(
	assessment?.requirements.filter((r) => r.source.regulation === run?.regulation).length ?? 0,
);
const counter = new Tween(0, { duration: 900, easing: cubicOut });
$effect(() => {
	counter.set(regulationCount, { duration: counter.current === 0 ? 0 : 900 });
});

const cites = $derived(
	assessment?.regulations.find((d) => d.regulation === run?.regulation)?.version,
);

async function apply() {
	if (!assessment || !run) return;
	applying = true;
	try {
		assessment = await api.applyUpdate(assessment.id, run.id);
		run.applied = true;
	} finally {
		applying = false;
	}
}

async function undo() {
	if (!assessment || !run) return;
	assessment = await api.undoUpdate(assessment.id, run.id);
	run.applied = false;
}

function scrollTo(id: string, highlight?: string) {
	document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'center' });
	if (highlight) {
		flash = highlight;
		setTimeout(() => {
			if (flash === highlight) flash = null;
		}, 1600);
	}
}

function openHunk(h: Hunk) {
	if (!run) return;
	const r = run;
	reading = { list: shown.map((x) => hunkReading(r, x)), index: shown.indexOf(h) };
}

function openChange(c: RequirementChange) {
	if (!run) return;
	const r = run;
	const list = r.changes.map((x) => changeReading(r, x)).filter((x): x is Reading => !!x);
	reading = {
		list,
		index: Math.max(
			0,
			list.findIndex((x) => x.id === changeId(c)),
		),
	};
}

const kindLabel: Record<ChangeKind, string> = {
	modified: 'Modified',
	removed: 'Removed',
	added: 'Added',
};
const plural = (n: number, word: string) => `${n} ${word}${n === 1 ? '' : 's'}`;
</script>

<svelte:head
	><title>{run ? `${run.regulation} ${run.toVersion}` : 'Update'} | sudo</title></svelte:head
>

{#if assessment}
	<AssessmentHeader {assessment}>
		<a href="/a/{assessment.id}/updates" class="ui-btn">All cited regulations</a>
	</AssessmentHeader>
{/if}

{#if missing}
	<p class="pt-6 text-sm">
		This comparison is not on file. <a href="/a/{params.id}/updates" class="ui-link">Start one</a>
	</p>
{:else if run && assessment}
	{@const added = byKind.added.length}
	<div class="min-h-0 flex-1 overflow-auto pb-16" id="run-scroll">
		<!-- Summary -->
		<section class="ui-grid items-end pt-6 pb-8">
			<div class="col-span-5">
				<div class="ui-label">{run.regulation}, {run.title}</div>
				<h1 class="ui-display mt-2 text-6xl">
					From {run.fromVersion} to <em class="text-accent">{run.toVersion}</em>
				</h1>
				<p class="mt-3 font-mono text-[12px] text-muted tabular-nums">
					{run.fileName},
					{run.identifiedBy === 'sha256'
						? 'matched by SHA-256'
						: run.identifiedBy === 'first page'
							? 'identified from its first page'
							: 'from the corpus'}
				</p>
			</div>
			<div class="col-span-4 grid grid-cols-3 gap-x-4 xl:gap-x-6">
				{#each [
					['Paragraphs amended', run.stats.amended],
					['New', run.stats.new],
					['Deleted', run.stats.deleted],
				] as const as [label, value] (label)}
					<div class="border-t-2 border-line pt-2">
						<div class="text-7xl leading-[0.85] font-light text-accent tabular-nums">{value}</div>
						<div class="mt-2 text-xs font-bold">{label}</div>
					</div>
				{/each}
			</div>
			<div class="col-span-3 flex flex-col items-end gap-3">
				<div class="text-right">
					<div class="ui-label">{short(run.regulation)} requirements</div>
					<div class="text-5xl leading-none font-light text-accent tabular-nums">
						{Math.round(counter.current)}
					</div>
					<div class="mt-1 font-mono text-[12px] text-muted tabular-nums">cites {cites}</div>
				</div>
				<div class="flex items-center gap-2">
					<a href="/a/{assessment.id}/graph?update={run.id}" class="ui-btn">See it in the graph</a>
					{#if run.applied}
						<span class="flex h-8 items-center gap-2 px-3 text-sm font-bold">
							<span class="size-2.5 bg-mark"></span>Applied
						</span>
					{:else}
						<button
							type="button"
							class="ui-btn ui-btn-primary"
							disabled={applying || cites !== run.fromVersion}
							onclick={apply}
						>
							{applying ? 'Applying' : 'Apply update'}
						</button>
					{/if}
				</div>
				{#if run.applied}
					<button type="button" class="ui-link text-xs text-muted" onclick={undo}>Undo</button>
				{/if}
			</div>
			<p class="col-span-9 mt-6 text-xl leading-snug font-medium">
				{run.stats.changedCitedParagraphs}
				of this assessment's {run.stats.citedParagraphs} cited
				{short(run.regulation)}
				paragraphs changed.
				{#if added}
					<strong class="font-bold">{plural(added, 'new obligation')} may apply.</strong>
				{:else}
					No new obligations in the sections it cites.
				{/if}
			</p>
		</section>

		<!-- Regulation diff -->
		<section class="ui-grid border-t border-line pt-4">
			<div class="col-span-12 mb-4 flex items-baseline gap-6">
				<h2 class="text-sm font-bold">What changed in {run.regulation}</h2>
				<p class="font-mono text-[12px] text-muted tabular-nums">
					{plural(run.hunks.length, 'changed paragraph')}. Unchanged text, formatting and
					{plural(run.stats.renumbered, 'renumbered paragraph')}
					left out.
				</p>
				<div class="ml-auto flex">
					<button
						type="button"
						class="ui-toggle {split ? '' : 'ui-toggle-on'}"
						aria-pressed={!split}
						onclick={() => (split = false)}
					>
						Unified
					</button>
					<button
						type="button"
						class="ui-toggle {split ? 'ui-toggle-on' : ''}"
						aria-pressed={split}
						onclick={() => (split = true)}
					>
						Split
					</button>
				</div>
			</div>

			<nav class="col-span-3" aria-label="Changed paragraphs">
				<div class="sticky top-2 max-h-[calc(100vh-10rem)] overflow-y-auto pr-2">
					<ol class="border-t-2 border-line-strong">
						{#each shown as h, i (h.id)}
							{#if i === relevantCount && relevantCount > 0}
								<li class="ui-label pt-4 pb-1">Not cited</li>
							{/if}
							<li class="ui-rule-soft border-b">
								<button
									type="button"
									class="flex w-full cursor-pointer items-baseline gap-2 py-1.5 text-left hover:bg-fg/5"
									onclick={() => scrollTo(`hunk-${h.id}`)}
								>
									<span
										class="size-2 shrink-0 self-center {h.status === 'new'
											? 'bg-mark'
											: h.status === 'deleted'
												? 'border border-muted'
												: 'bg-accent'}"
									></span>
									<span
										class="min-w-0 flex-1 truncate font-mono text-[12px] tabular-nums {h.status ===
										'deleted'
											? 'text-muted line-through'
											: ''}"
										>{paragraphName(h.label)}</span
									>
									<span class="font-mono text-[11.5px] text-accent tabular-nums"
										>+{h.addedWords}</span
									>
									<span class="w-9 text-right font-mono text-[11.5px] text-muted tabular-nums"
										>−{h.removedWords}</span
									>
								</button>
							</li>
						{/each}
					</ol>
					{#if relevantCount > 0 &&
						relevantCount < ordered.length &&
						ordered.length > SHOW_ALL_UP_TO}
						<button
							type="button"
							class="ui-link mt-3 cursor-pointer text-xs"
							onclick={() => (showAll = !showAll)}
						>
							{showAll
								? `Show only the ${relevantCount} that touch this assessment`
								: `Show ${ordered.length - relevantCount} more, not cited`}
						</button>
					{/if}
				</div>
			</nav>

			<div class="col-span-9 min-w-0">
				{#each shown as h (h.id)}
					<HunkView
						hunk={h}
						regulation={run.regulation}
						{split}
						fromVersion={run.fromVersion}
						toVersion={run.toVersion}
						onopen={() => openHunk(h)}
						onchange={(id) => scrollTo(`change-${id}`, id)}
					/>
				{/each}
			</div>
		</section>

		<!-- Requirement impact -->
		<section class="ui-grid mt-10 border-t border-line pt-4" id="impact">
			<div class="col-span-12 mb-2 flex items-baseline gap-6">
				<h2 class="text-sm font-bold">What it does to this assessment's requirements</h2>
				<p class="font-mono text-[12px] text-muted tabular-nums">
					{byKind.modified.length}
					modified, {byKind.removed.length} removed, {byKind.added.length} added
				</p>
			</div>
			{#each changeKinds as kind (kind)}
				{@const rows = byKind[kind]}
				<div class="col-span-12 mt-4">
					<div class="flex items-baseline gap-3 border-b-2 border-line-strong pb-1">
						<span class="text-3xl leading-none font-light text-accent tabular-nums"
							>{rows.length}</span
						>
						<span class="text-sm font-bold">{kindLabel[kind]}</span>
					</div>

					<ol>
						{#each rows as c (changeId(c))}
							{@const id = changeId(c)}
							<li
								id="change-{id}"
								class="ui-rule-soft grid scroll-mt-24 grid-cols-12 gap-x-4 border-b py-4 transition-colors duration-500 xl:gap-x-6 {flash ===
								id
									? 'bg-select'
									: ''}"
							>
								<span class="col-span-1 font-mono text-[12px] font-bold tabular-nums">{id}</span>
								<div class="col-span-7 text-[14px]">
									{#if c.change === 'modified'}
										<WordDiff before={c.oldText} after={c.newText} />
									{:else if c.change === 'removed'}
										<p
											class="border-l-2 border-line-strong pl-3 leading-relaxed text-muted line-through decoration-1"
										>
											{c.oldText}
										</p>
									{:else}
										<p class="border-l-2 border-mark pl-3 leading-relaxed">{c.newText}</p>
									{/if}
								</div>
								<div class="col-span-4 space-y-2 text-xs">
									<p class="leading-snug">{c.reason}</p>
									<p
										class="flex flex-wrap items-baseline gap-x-4 font-mono text-[12px] tabular-nums"
									>
										{#if c.source}
											<button
												type="button"
												class="ui-link cursor-pointer"
												onclick={() => openChange(c)}
											>
												{run.toVersion}, p. {c.source.page}, {paragraphName(c.source.paragraph)}
											</button>
										{:else if c.oldParagraph}
											<span class="text-muted"
												>was {paragraphName(c.oldParagraph)} in {run.fromVersion}</span
											>
										{/if}
										{#if c.hunk}
											<button
												type="button"
												class="ui-link cursor-pointer text-muted"
												onclick={() => scrollTo(`hunk-${c.hunk}`)}
											>
												See the diff
											</button>
										{/if}
									</p>
								</div>
							</li>
						{/each}
					</ol>
				</div>
			{/each}
		</section>
	</div>
{/if}

{#if reading}
	<PdfDrawer list={reading.list} bind:index={reading.index} onclose={() => (reading = null)} />
{/if}
