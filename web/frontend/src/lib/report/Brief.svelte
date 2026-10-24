<script lang="ts">
import { onMount } from 'svelte';
import { api } from '#lib/api/client.ts';
import type { Brief, Requirement } from '#lib/api/types.ts';
import { pdfHref } from './pdf.ts';

let { requirements }: { requirements: Requirement[] } = $props();

let brief = $state<Brief | null>(null);
let error = $state('');
/** The open citation: a paragraph label cited by one sentence. */
let open = $state<{ section: number; sentence: number; label: string } | null>(null);

const byId = $derived(new Map(requirements.map((r) => [r.id, r])));

onMount(async () => {
	try {
		brief = await api.getBrief(requirements);
	} catch (e) {
		error = e instanceof Error ? e.message : String(e);
	}
});

function label(req: Requirement) {
	return `${req.source.regulation.replace(/^UN /, '')} ${req.source.paragraph}`;
}

/** A sentence's cited requirements, one group per regulation paragraph. */
function citations(cites: string[]) {
	const groups = new Map<string, Requirement[]>();
	for (const id of cites) {
		const req = byId.get(id);
		if (!req) continue;
		groups.set(label(req), [...(groups.get(label(req)) ?? []), req]);
	}
	return [...groups];
}

function isOpen(section: number, sentence: number, label: string) {
	return open?.section === section && open.sentence === sentence && open.label === label;
}

function toggle(section: number, sentence: number, label: string) {
	open = isOpen(section, sentence, label) ? null : { section, sentence, label };
}
</script>

<section class="brief">
	<h2>Developer brief</h2>
	{#if brief}
		<p class="lead">
			What the component must meet, in short. Each citation opens the regulation text it rests on.
		</p>
		{#each brief.sections as section, si (section.title)}
			<div class="topic">
				<h3>{section.title}</h3>
				<div>
					<p class="prose">
						{#each section.sentences as sentence, ti (ti)}
							{sentence.text}
							{#each citations(sentence.cites) as [paragraph, reqs] (paragraph)}
								<button
									type="button"
									class="cite"
									class:active={isOpen(si, ti, paragraph)}
									aria-expanded={isOpen(si, ti, paragraph)}
									title="{reqs[0].source.regulation} paragraph {reqs[0].source
										.paragraph}, page {reqs[0].source.page}"
									onclick={() => toggle(si, ti, paragraph)}
								>
									{paragraph}
								</button>
							{/each}
							{' '}
						{/each}
					</p>
					{#if open?.section === si}
						{@const current = open}
						{@const reqs =
							citations(section.sentences[current.sentence].cites).find(
								([paragraph]) => paragraph === current.label,
							)?.[1] ?? []}
						{#each reqs as req (req.id)}
							{@const href = pdfHref(req.source)}
							<blockquote>
								<p class="source">
									<span class="strong">{req.source.regulation}</span>
									<span>Version {req.source.version}</span>
									<span>Paragraph {req.source.paragraph}</span>
									<span>Page {req.source.page}</span>
								</p>
								<p class="passage">{req.text}</p>
								<p class="links">
									{#if href}
										<a {href} target="_blank" rel="noreferrer"
											>Open page {req.source.page} of the PDF</a
										>
									{/if}
									<a href="#req-{req.id}">Show {req.id} in the requirement list</a>
								</p>
							</blockquote>
						{/each}
					{/if}
				</div>
			</div>
		{/each}
	{:else if error}
		<p class="status">The brief could not be written. {error}</p>
	{:else}
		<p class="status">
			Writing the brief from {requirements.length} requirements. The first time takes a minute or
			two.
		</p>
	{/if}
</section>

<style>
.lead,
.status {
	margin-left: 30mm;
	font-size: 9pt;
}
.status {
	color: var(--color-cv-ink-800);
}
.topic {
	display: grid;
	grid-template-columns: 30mm 1fr;
	padding: 2.5mm 0;
	border-bottom: 0.5pt solid rgb(0 0 0 / 0.2);
	break-inside: avoid;
}
.topic:first-of-type {
	margin-top: 3mm;
	border-top: 1.5pt solid black;
}
h3 {
	padding-right: 3mm;
	font-size: 9pt;
	font-weight: 700;
	line-height: 1.4;
}
.prose {
	font-size: 10.5pt;
	line-height: 1.6;
}
.cite {
	display: inline-block;
	margin-left: 0.8mm;
	padding: 0 0.8mm;
	border: 0.5pt solid currentColor;
	border-radius: var(--radius-control);
	font-size: 7.5pt;
	font-weight: 600;
	line-height: 1.5;
	vertical-align: 0.15em;
	white-space: nowrap;
	font-variant-numeric: tabular-nums;
	color: var(--color-cv-teal-700);
	cursor: pointer;
}
.cite:hover,
.cite.active {
	background: var(--color-cv-mint-300);
	border-color: var(--color-cv-mint-300);
	color: black;
}
blockquote {
	margin-top: 2mm;
	padding: 1.5mm 0 1.5mm 3mm;
	border-left: 1.5pt solid var(--color-cv-mint-300);
	font-size: 9pt;
}
.source,
.links {
	display: flex;
	flex-wrap: wrap;
	gap: 0 4mm;
	font-size: 8.5pt;
}
.strong {
	font-weight: 700;
}
.passage {
	margin: 1mm 0;
	font-size: 10pt;
	line-height: 1.45;
}
.links a {
	text-decoration: underline;
	text-underline-offset: 2px;
}
.links a:hover {
	color: var(--color-cv-teal-700);
}

@media print {
	.cite {
		border: none;
		padding: 0;
		color: var(--color-cv-teal-700);
	}
	blockquote {
		display: none;
	}
}
</style>
