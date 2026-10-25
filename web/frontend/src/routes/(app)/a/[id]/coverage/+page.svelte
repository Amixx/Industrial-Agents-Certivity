<script lang="ts">
import { cubicOut } from 'svelte/easing';
import { Tween } from 'svelte/motion';
import { slide } from 'svelte/transition';
import { api } from '#lib/api/client.ts';
import {
	type Coverage,
	type Extra,
	getCoverage,
	type Miss,
	type MissReason,
	type NearCut,
} from '#lib/api/coverage.ts';
import type { Assessment, Requirement, Source } from '#lib/api/types.ts';
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
const rolled = { matched: roll(), f2: roll() };

$effect(() => {
	const id = params.id;
	api.getAssessment(id).then((a) => (assessment = a));
	getCoverage(id)
		.then((c) => (coverage = c))
		.catch((e) => (failed = e instanceof Error ? e.message : String(e)));
});

const upload = $derived(coverage?.platform?.uploads.at(-1));
/** The platform's count where it scored this exact list, else sudo's own check. */
const headline = $derived.by(() => {
	const local = coverage?.local;
	if (!local) return null;
	if (upload?.matched != null) return { matched: upload.matched, f2: upload.f2, platform: true };
	return { matched: local.matched, f2: local.f2, platform: false };
});

$effect(() => {
	if (!headline) return;
	rolled.matched.target = headline.matched;
	rolled.f2.target = headline.f2;
});

const groups: { reason: MissReason; title: string; note: string }[] = [
	{
		reason: 'below_cut',
		title: 'Not in your list',
		note: 'sudo read these paragraphs but judged them not relevant enough to include. Check whether they apply to your product.',
	},
	{
		reason: 'split_finer',
		title: 'In your list, as fewer requirements',
		note: 'The expert wrote one requirement per table row or list item, sudo one for the whole paragraph. Check that the detail is covered.',
	},
	{
		reason: 'worded_differently',
		title: 'In your list, worded differently',
		note: 'sudo has a requirement on the same paragraph in other words. Compare the two.',
	},
];

let open = $state<string | null>(null);
let openRegs = $state<Record<string, boolean>>({});
let reading = $state<{ list: Requirement[]; index: number } | null>(null);

const read = (id: string, text: string, source: Source) =>
	(reading = { list: [{ id, text, source }], index: 0 });

const pct = (x: number) => `${(x * 100).toFixed(1)}%`;
const relevance = (n: { score: number; cut?: number }) =>
	`Relevance ${pct(n.score)}${n.cut != null ? `, needs ${pct(n.cut)}` : ''}`;

/** The platform's score against the held-out case's hidden answer, in words. */
const hiddenScore = $derived.by(() => {
	if (!upload) return '';
	const parts = [`F2 ${upload.f2.toFixed(3)}`];
	if (upload.recall != null)
		parts.push(`about ${Math.round(upload.recall * 100)}% of the expert's requirements covered`);
	if (upload.precision != null)
		parts.push(`${Math.round(upload.precision * 100)}% of your requirements also on its list`);
	return `The Certivity challenge platform scored this list against its own hidden expert answer on ${upload.at}: ${parts.join(', ')}.`;
});
const where = (s: Source) => `${s.regulation} § ${s.paragraph}, page ${s.page}`;

/** The decision's own reason, without the scope summary the pipeline appends in brackets. */
const plainReason = (reason: string) => reason.replace(/\s\([^()]*Scope:[\s\S]*$/, '');

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

/** Rows the platform's judge left unpaired, from its F2 and recall (F2 = 5PR / (4P + R)). */
const platformExtra = $derived.by(() => {
	const local = coverage?.local;
	if (!local || upload?.matched == null || !coverage?.platform) return null;
	const r = upload.matched / local.expected;
	const p = (upload.f2 * r) / (5 * r - 4 * upload.f2);
	return coverage.platform.rows - Math.round(p * coverage.platform.rows);
});

const underCut = $derived(coverage?.nearCut.filter((n) => !n.kept) ?? []);
const leastSure = $derived(coverage?.nearCut.filter((n) => n.kept) ?? []);
</script>

<svelte:head><title>Coverage | sudo</title></svelte:head>

{#if assessment}
	<AssessmentHeader {assessment} />
{/if}

{#snippet bar(matched: number, total: number)}
	<div class="flex h-2 w-full gap-px" aria-hidden="true">
		<div class="bg-accent" style="width: {(matched / total) * 100}%"></div>
		<div class="flex-1 bg-line-strong"></div>
	</div>
{/snippet}

{#snippet heading(label: string, title: string, note: string, count?: number)}
	<div class="col-span-12 mb-4 lg:col-span-3 lg:mb-0 lg:pr-6">
		<span class="ui-label">{label}</span>
		{#if count != null}
			<div class="ui-numeral mt-3">{count}</div>
		{/if}
		<h2 class="mt-2 text-base font-bold">{title}</h2>
		<p class="mt-2 text-xs leading-relaxed text-muted">{note}</p>
	</div>
{/snippet}

{#snippet missRow(m: Miss)}
	{@const isOpen = open === m.id}
	<li class="ui-rule-soft border-b">
		<button
			type="button"
			class="grid w-full cursor-pointer grid-cols-9 gap-x-4 py-3 text-left hover:bg-fg/5 xl:gap-x-6"
			aria-expanded={isOpen}
			onclick={() => (open = isOpen ? null : m.id)}
		>
			<span class="col-span-9 font-mono text-[12px] text-muted tabular-nums md:col-span-2">
				{m.source.regulation}
				§ {m.source.paragraph}
			</span>
			<span
				class="col-span-9 text-[13px] leading-relaxed md:col-span-5 {isOpen ? '' : 'line-clamp-2'}"
				>{m.text}</span
			>
			<span class="col-span-9 text-[12px] text-muted md:col-span-2 md:text-right">
				{#if m.reason === 'below_cut'}
					{#if m.score != null && m.cut != null}
						<span title="Score {m.score}, threshold {m.cut}"
							>{relevance({ score: m.score, cut: m.cut })}</span
						>
					{:else}
						No requirement on this paragraph
					{/if}
				{:else if m.nearest}
					Yours: {m.nearest.id}
				{/if}
			</span>
		</button>
		{#if isOpen}
			<div
				class="grid grid-cols-9 gap-x-4 pt-1 pb-5 xl:gap-x-6"
				transition:slide={{ duration: still ? 0 : 180 }}
			>
				<div class="col-span-9 border-t-2 border-accent pt-2 md:col-span-4 md:col-start-3">
					<span class="ui-label">Expert's requirement</span>
					<p class="mt-2 text-[13px] leading-relaxed">{m.text}</p>
					<p class="mt-2 font-mono text-[12px] text-muted">{where(m.source)}</p>
				</div>
				<div class="col-span-9 mt-4 border-t-2 border-line-strong pt-2 md:col-span-3 md:mt-0">
					{#if m.nearest}
						<span class="ui-label">Yours, {m.nearest.id}</span>
						<p class="mt-2 text-[13px] leading-relaxed">{m.nearest.text}</p>
						{#if m.nearest.pairedWith}
							<p class="mt-2 text-xs text-muted">
								This requirement already covers another expert requirement, {m.nearest.pairedWith}.
							</p>
						{/if}
					{:else}
						<span class="ui-label">Yours</span>
						<p class="mt-2 text-[13px] leading-relaxed text-muted">
							No requirement in your list cites this paragraph.
						</p>
					{/if}
				</div>
				<div class="col-span-9 mt-4 md:col-span-7 md:col-start-3">
					<button type="button" class="ui-btn" onclick={() => read(m.id, m.text, m.source)}>
						Read the paragraph
					</button>
				</div>
			</div>
		{/if}
	</li>
{/snippet}

{#snippet paragraphRow(n: NearCut)}
	<li class="ui-rule-soft grid grid-cols-9 items-start gap-x-4 border-b py-3 xl:gap-x-6">
		<span class="col-span-9 font-mono text-[12px] text-muted tabular-nums md:col-span-2">
			{n.source.regulation}
			§ {n.source.paragraph}
			<span class="block">page {n.source.page}</span>
		</span>
		<span class="col-span-9 line-clamp-3 text-[13px] leading-relaxed md:col-span-5"
			>{n.text ?? ''}</span
		>
		<span class="col-span-9 flex items-center gap-3 md:col-span-2 md:flex-col md:items-end">
			<span
				class="text-[12px] text-muted tabular-nums"
				title="Score {n.score}{n.cut != null ? `, threshold ${n.cut}` : ''}"
			>
				{relevance(n)}
			</span>
			<button
				type="button"
				class="ui-btn"
				onclick={() => read(`§ ${n.source.paragraph}`, n.text ?? '', n.source)}
			>
				Read
			</button>
		</span>
	</li>
{/snippet}

{#snippet borderline(label: string)}
	{#if underCut.length || leastSure.length}
		<section class="ui-grid ui-section mt-12">
			{@render heading(
				label,
				'Paragraphs worth a second look',
				"sudo's relevance score is its estimate that an expert would cite the paragraph for this product. These paragraphs sit closest to the score it needs to include one.",
			)}
			<div class="col-span-12 lg:col-span-9">
				{#if underCut.length}
					<p class="text-lg font-medium">Just left out</p>
					<p class="text-sm text-muted">
						Not in your list. If one applies to your product, add its requirements.
					</p>
					<ol class="mt-3 border-t-2 border-line">
						{#each underCut as n (`${n.source.regulation} ${n.source.paragraph}`)}
							{@render paragraphRow(n)}
						{/each}
					</ol>
				{/if}
				{#if leastSure.length}
					<p class="mt-10 text-lg font-medium">Included with the least certainty</p>
					<p class="text-sm text-muted">In your list. Check that they apply.</p>
					<ol class="mt-3 border-t-2 border-line">
						{#each leastSure as n (`${n.source.regulation} ${n.source.paragraph}`)}
							{@render paragraphRow(n)}
						{/each}
					</ol>
				{/if}
			</div>
		</section>
	{/if}
{/snippet}

<div class="min-h-0 flex-1 overflow-auto pb-16">
	{#if failed}
		<p class="ui-section mt-6 text-sm">The coverage could not be computed: {failed}</p>
	{:else if !coverage}
		<p class="ui-section mt-6 text-sm text-muted">Comparing with the expert's answer…</p>
	{:else if coverage.hasAnswer && coverage.local && headline}
		{@const local = coverage.local}
		{@const missing = local.expected - headline.matched}
		{#if coverage.expertCopies === local.expected}
			<p class="ui-section mt-6 text-sm">
				This assessment holds all {local.expected} expert requirements word for word, so the numbers
				below say nothing about sudo.
				{#if coverage.engineRun}
					<a class="ui-link" href="/a/{coverage.engineRun}/coverage"
						>See sudo's own run on this product</a
					>.
				{/if}
			</p>
		{/if}

		<!-- 1. How complete the list is -->
		<section class="ui-grid ui-section mt-6">
			{@render heading(
				'01 Completeness',
				"Compared with an expert's answer",
				'Certivity published the requirements an expert listed for this product. This page compares your list with them.',
			)}
			<div class="col-span-12 lg:col-span-9">
				<div class="flex flex-wrap items-end gap-x-14 gap-y-6">
					<div>
						<div class="flex items-baseline gap-3">
							<span class="ui-count text-[clamp(4.5rem,7vw,7.5rem)]"
								>{Math.round(rolled.matched.current)}</span
							>
							<span class="ui-display text-4xl text-muted">of {local.expected}</span>
						</div>
						<p class="mt-2 max-w-[30ch] text-sm">expert requirements are covered by your list</p>
					</div>
					<div>
						<span class="ui-count text-[clamp(4.5rem,7vw,7.5rem)]"
							>{rolled.f2.current.toFixed(3)}</span
						>
						<p class="mt-2 max-w-[34ch] text-sm">
							F2, one score for the whole list that weighs a missed requirement four times an extra
							one
						</p>
					</div>
				</div>
				<div class="mt-6 max-w-[64rem]">
					{@render bar(headline.matched, local.expected)}
					<div class="mt-2 flex justify-between text-[12px] text-muted tabular-nums">
						<span>{headline.matched} covered</span>
						<span>{missing} missing</span>
					</div>
				</div>
				<p class="mt-5 max-w-[72ch] text-xs leading-relaxed text-muted">
					{#if headline.platform && upload}
						Scored by the Certivity challenge platform, which judges with a language model, on
						{upload.at}. sudo's own check is stricter: it matches by shared wording and finds
						{local.matched}
						of {local.expected}. The lists below come from that check, because the platform does not
						say which requirements it missed.
					{:else}
						Scored by sudo's own check, which matches requirements by shared wording within each
						regulation. The challenge platform has not scored this exact list.
					{/if}
				</p>
				<p class="mt-8 max-w-[60ch] text-xl leading-tight font-medium">
					sudo leans toward including: a requirement you miss costs more than an extra one you
					strike out.
				</p>
			</div>
		</section>

		<!-- 2. What may be missing -->
		<section class="ui-grid ui-section mt-14">
			{@render heading(
				'02 To check',
				'Expert requirements not matched',
				"Each with the reason it was not matched. Open one to compare it with your list and read the regulation's paragraph.",
				coverage.missed.length,
			)}
			<div class="col-span-12 lg:col-span-9">
				{#each groups as g (g.reason)}
					{@const rows = coverage.missed.filter((m) => m.reason === g.reason)}
					{#if rows.length}
						<div class="mb-10">
							<div class="flex items-baseline gap-5 border-b-2 border-line pb-2">
								<span class="ui-count w-16 shrink-0 text-5xl">{rows.length}</span>
								<div>
									<p class="text-lg font-medium">{g.title}</p>
									<p class="max-w-[80ch] text-sm text-muted">{g.note}</p>
								</div>
							</div>
							<ol>
								{#each rows as m (m.id)}
									{@render missRow(m)}
								{/each}
							</ol>
						</div>
					{/if}
				{/each}
			</div>
		</section>

		<!-- 3. Extra requirements -->
		<section class="ui-grid ui-section mt-4">
			{@render heading(
				'03 To strike out',
				'Requirements the expert did not list',
				'In your list but not matched to any expert requirement. Review them and strike out what does not apply to your product.',
				coverage.extra.length,
			)}
			<div class="col-span-12 lg:col-span-9">
				<div class="flex flex-wrap gap-x-10 gap-y-4">
					<div class="border-t-2 border-line pt-2">
						<div class="ui-count text-4xl">{onExpert}</div>
						<p class="mt-1 max-w-[26ch] text-xs">
							on paragraphs the expert also cites, often one requirement split further
						</p>
					</div>
					<div class="border-t-2 border-line pt-2">
						<div class="ui-count text-4xl">{coverage.extra.length - onExpert}</div>
						<p class="mt-1 max-w-[26ch] text-xs">on paragraphs the expert does not cite</p>
					</div>
				</div>
				{#if platformExtra != null}
					<p class="mt-4 text-xs text-muted">
						The challenge platform, matching by meaning, counts {platformExtra}.
					</p>
				{/if}
				<ul class="mt-6 border-t-2 border-line">
					{#each extraByReg as [reg, rows] (reg)}
						{@const inside = rows.filter((e) => e.onExpertParagraph).length}
						<li class="ui-rule-soft border-b">
							<button
								type="button"
								class="flex w-full cursor-pointer items-baseline gap-6 py-3 text-left hover:bg-fg/5"
								aria-expanded={!!openRegs[reg]}
								onclick={() => (openRegs[reg] = !openRegs[reg])}
							>
								<span class="w-24 shrink-0 text-sm font-bold">{reg}</span>
								<span class="flex-1 text-[13px] text-muted tabular-nums">
									{rows.length}
									requirements, {inside} on the expert's paragraphs
								</span>
								<span class="text-xs text-muted">{openRegs[reg] ? 'Hide' : 'Show'}</span>
							</button>
							{#if openRegs[reg]}
								<ol class="pb-4" transition:slide={{ duration: still ? 0 : 180 }}>
									{#each rows as e (e.id)}
										<li class="grid grid-cols-9 gap-x-4 py-1.5 xl:gap-x-6">
											<span class="col-span-9 font-mono text-[12px] text-muted md:col-span-2">
												{e.id}, § {e.source.paragraph}
											</span>
											<span
												class="col-span-9 line-clamp-2 text-[13px] leading-relaxed md:col-span-5"
												>{e.text}</span
											>
											<span class="col-span-9 text-[12px] text-muted md:col-span-2 md:text-right">
												{e.onExpertParagraph ? 'Expert cites this paragraph' : ''}
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

		{@render borderline('04 Borderline')}
	{:else}
		<!-- No expert answer: what the user can still check. -->
		<section class="ui-grid ui-section mt-6">
			{@render heading(
				'01 Completeness',
				'No expert answer to compare with',
				'Certivity has not published an expert answer for this product, so this page cannot list what is missing.',
			)}
			<div class="col-span-12 lg:col-span-9">
				<p class="max-w-[52ch] text-xl leading-tight font-medium">
					Without an expert answer, the paragraphs below are where a review pays off most.
				</p>
				{#if upload}
					<p class="mt-5 max-w-[72ch] text-xs leading-relaxed text-muted">
						{hiddenScore}
					</p>
				{/if}
			</div>
		</section>
		{@render borderline('02 Borderline')}
	{/if}

	{#if coverage}
		<!-- Regulations not applied -->
		<section class="ui-grid ui-section mt-12">
			{@render heading(
				coverage.hasAnswer ? '05 Not applied' : '03 Not applied',
				'Regulations left out',
				'sudo considered these regulations and decided they do not apply. The reason is its own.',
				coverage.excluded.length,
			)}
			<ul class="col-span-12 border-t-2 border-line lg:col-span-9">
				{#each coverage.excluded as d (d.regulation)}
					<li class="ui-rule-soft flex gap-6 border-b py-2.5">
						<span class="w-24 shrink-0 text-sm font-bold">{d.regulation}</span>
						<span class="text-[13px] leading-relaxed">
							{#if d.title}
								<span class="text-muted">{d.title}.</span>
							{/if}
							{plainReason(d.reason)}
						</span>
					</li>
				{/each}
			</ul>
		</section>
	{/if}
</div>

{#if reading}
	<PdfDrawer list={reading.list} bind:index={reading.index} onclose={() => (reading = null)} />
{/if}
