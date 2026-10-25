<script lang="ts">
import { cubicOut } from 'svelte/easing';
import { Tween } from 'svelte/motion';
import { slide } from 'svelte/transition';
import { api } from '#lib/api/client.ts';
import {
	type Coverage,
	type CutStage,
	type Extra,
	getCoverage,
	type Miss,
	type MissReason,
} from '#lib/api/coverage.ts';
import type { Assessment, Requirement } from '#lib/api/types.ts';
import AssessmentHeader from '#lib/components/AssessmentHeader.svelte';
import PdfDrawer from '#lib/graph/PdfDrawer.svelte';
import type { PageProps } from './$types';

let { params }: PageProps = $props();

let assessment = $state<Assessment | null>(null);
let coverage = $state<Coverage | null>(null);
let failed = $state<string | null>(null);

const still =
	typeof matchMedia !== 'undefined' && matchMedia('(prefers-reduced-motion: reduce)').matches;
const roll = () => new Tween(0, { duration: still ? 0 : 900, easing: cubicOut });
const rolled = { matched: roll(), f2: roll(), extra: roll() };

$effect(() => {
	const id = params.id;
	api.getAssessment(id).then((a) => (assessment = a));
	getCoverage(id)
		.then((c) => (coverage = c))
		.catch((e) => (failed = e instanceof Error ? e.message : String(e)));
});

const upload = $derived(coverage?.platform?.uploads.at(-1));
const headline = $derived.by(() => {
	const local = coverage?.local;
	if (!local) return null;
	if (upload?.matched != null) return { matched: upload.matched, f2: upload.f2 };
	return { matched: local.matched, f2: local.f2 };
});

$effect(() => {
	if (!headline || !coverage) return;
	rolled.matched.target = headline.matched;
	rolled.f2.target = headline.f2;
	rolled.extra.target = coverage.extra.length;
});

const groups: { reason: MissReason; title: string; note: string }[] = [
	{
		reason: 'below_cut',
		title: 'Paragraph ranked below the cut',
		note: 'The engine scored it, but under the threshold.',
	},
	{
		reason: 'split_finer',
		title: 'Expert splits it finer',
		note: 'One expert row per table row or list item, one sudo row for the paragraph.',
	},
	{
		reason: 'worded_differently',
		title: 'Same paragraph, different wording',
		note: 'The judge did not pair them.',
	},
];

const stageLabel: Record<CutStage, string> = {
	paragraph: 'paragraph cut',
	section: 'section cut',
	confidence: 'confidence cut',
};

let open = $state<string | null>(null);
let reading = $state<{ list: Requirement[]; index: number } | null>(null);
let openRegs = $state<Record<string, boolean>>({});

/** "0.310, cut 0.3535, section cut": the score to three places, the cut as the run set it. */
const scoreText = (n: { score: number; cut?: number; stage?: CutStage }) =>
	[n.score.toFixed(3), n.cut != null && `cut ${n.cut}`, n.stage && stageLabel[n.stage]]
		.filter(Boolean)
		.join(', ');

const hiddenScore = $derived.by(() => {
	if (!upload || !coverage?.platform) return '';
	const parts = [`F2 ${upload.f2.toFixed(3)}`];
	if (upload.precision != null) parts.push(`precision ${upload.precision.toFixed(3)}`);
	if (upload.recall != null) parts.push(`recall ${upload.recall.toFixed(3)}`);
	const { file, rows } = coverage.platform;
	return `Against its hidden answer: ${parts.join(', ')}. ${file}, ${rows} rows.`;
});

const where = (s: Miss['source']) => `${s.regulation} / p. ${s.page} / § ${s.paragraph}`;

/** The decision's own reason, without the scope summary the pipeline appends in brackets. */
const plainReason = (reason: string) => reason.replace(/\s\([^()]*Scope:[\s\S]*$/, '');

/** Rows the platform's judge left unpaired, from its F2 and recall (F2 = 5PR / (4P + R)). */
const platformUnpaired = $derived.by(() => {
	const local = coverage?.local;
	if (!local || upload?.matched == null || !coverage?.platform) return null;
	const r = upload.matched / local.expected;
	const p = (upload.f2 * r) / (5 * r - 4 * upload.f2);
	return coverage.platform.rows - Math.round(p * coverage.platform.rows);
});

const extraByReg = $derived.by(() => {
	const by = new Map<string, Extra[]>();
	for (const e of coverage?.extra ?? []) {
		const list = by.get(e.source.regulation) ?? [];
		list.push(e);
		by.set(e.source.regulation, list);
	}
	return [...by.entries()].sort((a, b) => b[1].length - a[1].length);
});

const onExpert = $derived(coverage?.extra.filter((e) => e.onExpertParagraph).length ?? 0);
</script>

<svelte:head><title>Coverage | sudo</title></svelte:head>

{#if assessment}
	<AssessmentHeader {assessment} />
{/if}

{#snippet bar(matched: number, total: number, thick: boolean)}
	<div class="flex w-full gap-px {thick ? 'h-2' : 'h-1'}" aria-hidden="true">
		<div class="bg-accent" style="width: {(matched / total) * 100}%"></div>
		<div class="flex-1 bg-line-strong"></div>
	</div>
{/snippet}

{#snippet missRow(m: Miss)}
	{@const isOpen = open === m.id}
	<li class="ui-rule-soft border-b">
		<button
			type="button"
			class="grid w-full cursor-pointer grid-cols-10 gap-x-4 py-3 text-left hover:bg-fg/5 xl:gap-x-6"
			aria-expanded={isOpen}
			onclick={() => (open = isOpen ? null : m.id)}
		>
			<span class="col-span-2 font-mono text-[12px] text-muted tabular-nums">
				<span class="block font-bold text-fg">{m.id}</span>
				{where(m.source)}
			</span>
			<span class="col-span-6 text-[13px] leading-relaxed {isOpen ? '' : 'line-clamp-2'}"
				>{m.text}</span
			>
			<span class="col-span-2 text-right font-mono text-[12px] text-muted tabular-nums">
				{#if m.reason === 'below_cut'}
					{#if m.score != null && m.cut != null}
						<span class="text-fg">{scoreText({ score: m.score, cut: m.cut })}</span>
						<span class="block">{m.stage ? stageLabel[m.stage] : ''}</span>
					{:else}
						Never cited, score not kept by this run
					{/if}
				{:else if m.nearest}
					Similarity {m.nearest.similarity.toFixed(2)}
				{/if}
			</span>
		</button>
		{#if isOpen}
			<div
				class="grid grid-cols-10 gap-x-4 pt-1 pb-5 xl:gap-x-6"
				transition:slide={{ duration: still ? 0 : 180 }}
			>
				<div class="col-span-2"></div>
				<div class="col-span-4 border-t-2 border-accent pt-2">
					<span class="ui-label">Expert, {m.id}</span>
					<p class="mt-2 text-[13px] leading-relaxed">{m.text}</p>
				</div>
				<div class="col-span-4 border-t-2 border-line-strong pt-2">
					{#if m.nearest}
						<span class="ui-label"
							>sudo nearest on § {m.nearest.source.paragraph}, {m.nearest.id}</span
						>
						<p class="mt-2 text-[13px] leading-relaxed">{m.nearest.text}</p>
						<p class="mt-2 font-mono text-[12px] text-muted tabular-nums">
							Judge similarity {m.nearest.similarity.toFixed(2)}, pairs from 0.45.
							{#if m.nearest.pairedWith}
								The judge paired this row with {m.nearest.pairedWith} instead.
							{/if}
						</p>
					{:else}
						<span class="ui-label">sudo</span>
						<p class="mt-2 text-[13px] leading-relaxed text-muted">
							No requirement on this paragraph.
						</p>
					{/if}
				</div>
				<div class="col-span-2"></div>
				<div class="col-span-8 mt-4">
					<button type="button" class="ui-btn" onclick={() => (reading = { list: [m], index: 0 })}>
						Read the paragraph
					</button>
				</div>
			</div>
		{/if}
	</li>
{/snippet}

<div class="min-h-0 flex-1 overflow-auto pb-16">
	{#if failed}
		<p class="ui-section mt-6 text-sm">The coverage could not be computed: {failed}</p>
	{:else if !coverage}
		<p class="ui-section mt-6 text-sm text-muted">Comparing with the expert's answer…</p>
	{:else if coverage.hasAnswer && coverage.local && headline}
		{@const local = coverage.local}
		{#if coverage.expertCopies === local.expected}
			<p class="ui-section mt-6 text-sm">
				This assessment holds all {local.expected} expert requirements word for word, so the scores
				below measure nothing about the engine.
				{#if coverage.engineRun}
					<a class="ui-link" href="/a/{coverage.engineRun}/coverage"
						>See the engine's run on this case</a
					>.
				{/if}
			</p>
		{/if}
		<!-- 1. Score -->
		<section class="ui-grid ui-section mt-6">
			<div class="col-span-12 mb-4 lg:col-span-2 lg:mb-0">
				<span class="ui-label">01 Score</span>
				<p class="mt-2 text-sm font-bold">Against the expert's answer</p>
				<p class="mt-1 font-mono text-[12px] text-muted">cases/{coverage.case}/expected.json</p>
			</div>
			<div class="col-span-12 lg:col-span-10 grid grid-cols-10 gap-x-4 xl:gap-x-6">
				<div class="col-span-10 xl:col-span-6">
					<div class="flex flex-wrap items-end gap-x-12 gap-y-4">
						<div>
							<div class="flex items-baseline gap-3">
								<span class="ui-count text-[clamp(4.5rem,7vw,7.5rem)]"
									>{Math.round(rolled.matched.current)}</span
								>
								<span class="ui-display text-4xl text-muted">of {local.expected}</span>
							</div>
							<p class="mt-2 text-sm">expert requirements matched</p>
						</div>
						<div>
							<span class="ui-count text-[clamp(4.5rem,7vw,7.5rem)]"
								>{rolled.f2.current.toFixed(3)}</span
							>
							<p class="mt-2 text-sm">F2</p>
						</div>
					</div>
					<div class="mt-5">
						{@render bar(headline.matched, local.expected, true)}
						<div class="mt-2 flex justify-between font-mono text-[12px] text-muted tabular-nums">
							<span>{headline.matched} matched</span>
							<span>{local.expected - headline.matched} missed</span>
						</div>
					</div>
					{#if upload}
						<span class="ui-label mt-4 text-accent">Challenge platform, uploaded {upload.at}</span>
						<span class="mt-1 block font-mono text-[12px] text-muted">
							{coverage.platform?.file}, {coverage.platform?.rows} rows, judged by a language model
						</span>
						{#if (coverage.platform?.uploads.length ?? 0) > 1}
							<span class="mt-1 block font-mono text-[12px] text-muted">
								{#each coverage.platform?.uploads.slice(0, -1) ?? [] as u (u.at)}
									Same file uploaded {u.at}: {u.matched} / {u.f2}.
								{/each}
							</span>
						{/if}
					{:else}
						<span class="ui-label mt-4">The challenge platform never scored this exact list</span>
						<span class="mt-1 block font-mono text-[12px] text-muted">
							The numbers above are the local judge's.
						</span>
					{/if}
				</div>
				{#if upload}
					<div class="col-span-10 mt-8 self-end xl:col-span-3 xl:col-start-8 xl:mt-0">
						<div class="flex items-baseline gap-6">
							<div>
								<span class="ui-count text-5xl">{local.matched}</span>
								<span class="text-sm text-muted">of {local.expected}</span>
							</div>
							<div>
								<span class="ui-count text-5xl">{local.f2.toFixed(3)}</span>
								<span class="text-sm text-muted">F2</span>
							</div>
						</div>
						<div class="mt-3">{@render bar(local.matched, local.expected, false)}</div>
						<span class="ui-label mt-4">Local judge, token overlap</span>
						<span class="mt-1 block font-mono text-[12px] text-muted tabular-nums">
							Precision {local.precision.toFixed(3)}, recall {local.recall.toFixed(3)},
							{local.submitted}
							rows
						</span>
						<span class="mt-1 block font-mono text-[12px] text-muted"
							>brain/eval/judge.py, no model</span
						>
					</div>
				{/if}
				<p class="col-span-10 mt-8 text-xl leading-tight font-medium">
					sudo leans toward recall: a missed requirement costs more than an extra one to strike out.
				</p>
			</div>
		</section>

		<!-- 2. Missed expert requirements -->
		<section class="ui-grid ui-section mt-14">
			<div class="col-span-12 mb-4 lg:col-span-2 lg:mb-0">
				<span class="ui-label">02 Missed</span>
				<div class="ui-numeral mt-3">{coverage.missed.length}</div>
				<p class="mt-2 text-sm font-bold">Expert requirements the local judge did not match</p>
				<p class="mt-2 text-xs leading-snug text-muted">
					{#if upload?.matched != null}
						The platform's judge missed {local.expected - upload.matched} and does not say which.
						This list is the local judge's, which pairs by token overlap and misses more.
					{:else}
						Matched one to one by token overlap within each regulation.
					{/if}
				</p>
			</div>
			<div class="col-span-12 lg:col-span-10">
				{#each groups as g (g.reason)}
					{@const rows = coverage.missed.filter((m) => m.reason === g.reason)}
					<div class="mb-10">
						<div
							class="grid grid-cols-10 items-baseline gap-x-4 border-b-2 border-line pb-2 xl:gap-x-6"
						>
							<span class="ui-count col-span-2 text-5xl">{rows.length}</span>
							<div class="col-span-8">
								<p class="text-lg font-medium">{g.title}</p>
								<p class="text-sm text-muted">{g.note}</p>
							</div>
						</div>
						<ol>
							{#each rows as m (m.id)}
								{@render missRow(m)}
							{/each}
						</ol>
					</div>
				{/each}
			</div>
		</section>

		<!-- 3. Rows the expert did not list -->
		<section class="ui-grid ui-section mt-4">
			<div class="col-span-12 mb-4 lg:col-span-2 lg:mb-0">
				<span class="ui-label">03 Extra</span>
				<div class="ui-numeral mt-3">{Math.round(rolled.extra.current)}</div>
				<p class="mt-2 text-sm font-bold">Rows the expert did not list</p>
				<p class="mt-2 text-xs leading-snug text-muted">
					sudo rows the local judge paired with no expert row.
					{#if platformUnpaired != null}
						The platform left {platformUnpaired} unpaired, from its F2 and recall.
					{/if}
				</p>
			</div>
			<div class="col-span-12 lg:col-span-10">
				<div class="grid grid-cols-10 gap-x-4 xl:gap-x-6">
					<div class="col-span-2 border-t-2 border-line pt-2">
						<div class="ui-count text-4xl">{onExpert}</div>
						<p class="mt-1 text-xs">on the expert's paragraphs</p>
					</div>
					<div class="col-span-2 border-t-2 border-line pt-2">
						<div class="ui-count text-4xl">{coverage.extra.length - onExpert}</div>
						<p class="mt-1 text-xs">on other paragraphs</p>
					</div>
					<p class="col-span-6 self-end text-sm leading-snug">
						We keep them. A missed requirement costs more than an extra one to strike out.
					</p>
				</div>
				<ul class="mt-6 border-t-2 border-line">
					{#each extraByReg as [reg, rows] (reg)}
						{@const inside = rows.filter((e) => e.onExpertParagraph).length}
						<li class="ui-rule-soft border-b">
							<button
								type="button"
								class="grid w-full cursor-pointer grid-cols-10 gap-x-4 py-3 text-left hover:bg-fg/5 xl:gap-x-6"
								aria-expanded={!!openRegs[reg]}
								onclick={() => (openRegs[reg] = !openRegs[reg])}
							>
								<span class="col-span-2 text-sm font-bold">{reg}</span>
								<span class="col-span-6 font-mono text-[12px] text-muted tabular-nums">
									{rows.length}
									rows: {inside} on the expert's paragraphs, {rows.length - inside} on others
								</span>
								<span class="col-span-2 text-right text-xs text-muted"
									>{openRegs[reg] ? 'Hide' : 'Show'}</span
								>
							</button>
							{#if openRegs[reg]}
								<ol class="pb-4" transition:slide={{ duration: still ? 0 : 180 }}>
									{#each rows as e (e.id)}
										<li class="grid grid-cols-10 gap-x-4 py-1.5 xl:gap-x-6">
											<span class="col-span-2 font-mono text-[12px] text-muted tabular-nums">
												{e.id}
												/ § {e.source.paragraph}
											</span>
											<span class="col-span-6 line-clamp-2 text-[13px] leading-relaxed"
												>{e.text}</span
											>
											<span class="col-span-2 text-right font-mono text-[12px] text-muted">
												{e.onExpertParagraph ? "Expert's paragraph" : 'Other paragraph'}
											</span>
										</li>
									{/each}
								</ol>
							{/if}
						</li>
					{/each}
				</ul>
			</div>
		</section>
	{:else}
		<!-- No expert answer: the paragraph cut stands in for the comparison. -->
		<section class="ui-grid ui-section mt-6">
			<div class="col-span-12 mb-4 lg:col-span-2 lg:mb-0">
				<span class="ui-label">01 Score</span>
			</div>
			<div class="col-span-12 lg:col-span-10">
				<p class="max-w-[48ch] text-xl leading-tight font-medium">
					There is no public expert answer for this case to compare against.
				</p>
				{#if upload}
					<span class="ui-label mt-6 text-accent">Challenge platform, uploaded {upload.at}</span>
					<p class="mt-2 font-mono text-[12px] text-muted tabular-nums">
						{hiddenScore}
					</p>
				{/if}
			</div>
		</section>
		<section class="ui-grid ui-section mt-12">
			<div class="col-span-12 mb-4 lg:col-span-2 lg:mb-0">
				<span class="ui-label">02 Near the cut</span>
				<p class="mt-2 text-sm font-bold">Paragraphs closest to the threshold</p>
				<p class="mt-2 text-xs leading-snug text-muted">
					The score is the engine's probability that an expert cites the paragraph.
				</p>
			</div>
			<div class="col-span-12 lg:col-span-10 grid grid-cols-10 gap-x-4 xl:gap-x-6">
				{#each [false, true] as kept (kept)}
					{@const rows = coverage.nearCut.filter((n) => n.kept === kept)}
					<div class="col-span-5">
						<p class="border-b-2 border-line pb-2 text-lg font-medium">
							{kept ? 'Kept, lowest scores' : 'Cut, highest scores'}
						</p>
						{#if !rows.length}
							<p class="py-3 text-sm text-muted">This run did not keep these scores.</p>
						{/if}
						<ol>
							{#each rows as n (`${n.source.regulation} ${n.source.paragraph}`)}
								<li
									class="ui-rule-soft flex justify-between gap-4 border-b py-2 font-mono text-[12px] tabular-nums"
								>
									<span>{where(n.source)}</span>
									<span class={kept ? '' : 'text-muted'}>
										{scoreText(n)}
									</span>
								</li>
							{/each}
						</ol>
					</div>
				{/each}
			</div>
		</section>
	{/if}

	{#if coverage}
		<!-- 4. Regulations left out on purpose -->
		<section class="ui-grid ui-section mt-12">
			<div class="col-span-12 mb-4 lg:col-span-2 lg:mb-0">
				<span class="ui-label">{coverage.hasAnswer ? '04' : '03'} Left out</span>
				<div class="ui-numeral mt-3">{coverage.excluded.length}</div>
				<p class="mt-2 text-sm font-bold">Regulations left out on purpose</p>
				<p class="mt-2 text-xs leading-snug text-muted">The regulation pick's own reasons.</p>
			</div>
			<ul class="col-span-12 border-t-2 border-line lg:col-span-10">
				{#each coverage.excluded as d (d.regulation)}
					<li class="ui-rule-soft grid grid-cols-10 gap-x-4 border-b py-2.5 xl:gap-x-6">
						<span class="col-span-2 text-sm font-bold">{d.regulation}</span>
						<span class="col-span-8 text-[13px] leading-relaxed">{plainReason(d.reason)}</span>
					</li>
				{/each}
			</ul>
		</section>
	{/if}
</div>

{#if reading}
	<PdfDrawer list={reading.list} bind:index={reading.index} onclose={() => (reading = null)} />
{/if}
