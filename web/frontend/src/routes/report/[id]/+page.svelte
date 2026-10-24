<script lang="ts">
import { onMount } from 'svelte';
import { api } from '#lib/api/client.ts';
import type { Assessment } from '#lib/api/types.ts';
import Cover from '#lib/report/Cover.svelte';
import Profile from '#lib/report/Profile.svelte';
import Regulations from '#lib/report/Regulations.svelte';
import RequirementGroup from '#lib/report/RequirementGroup.svelte';
import { page } from '$app/state';

const id = $derived(page.params.id ?? '');

let assessment = $state<Assessment | null>(null);
let loaded = $state(false);

onMount(async () => {
	assessment = await api.getAssessment(id);
	loaded = true;
});

const groups = $derived.by(() => {
	if (!assessment) return [];
	const map = new Map(assessment.regulations.map((r) => [r.regulation, r.title]));
	const byReg = new Map<string, Assessment['requirements']>();
	for (const req of assessment.requirements) {
		const list = byReg.get(req.source.regulation) ?? [];
		list.push(req);
		byReg.set(req.source.regulation, list);
	}
	return [...byReg].map(([regulation, requirements]) => ({
		regulation,
		title: map.get(regulation) ?? '',
		requirements,
	}));
});

const caseLabel = $derived(assessment?.caseName ?? assessment?.profile.productType ?? '');
const pageCaseCss = $derived(caseLabel.replace(/[^\p{L}\p{N} ._-]/gu, ''));
</script>

<svelte:head>
	<title>{assessment ? `sudo report | ${caseLabel}` : 'sudo report'}</title>
	<link rel="preconnect" href="https://fonts.googleapis.com">
	<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous">
	<link
		rel="stylesheet"
		href="https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@300;400;500;600;700;800&display=swap"
	>
	{@html `<style>
		@page {
			size: A4;
			margin: 18mm 16mm 20mm;
			@bottom-left {
				content: 'sudo';
				font: 700 8pt 'Hanken Grotesk', Arial, sans-serif;
				color: #000;
			}
			@bottom-center {
				content: '${pageCaseCss}';
				font: 8pt 'Hanken Grotesk', Arial, sans-serif;
				color: #000;
			}
			@bottom-right {
				content: 'Page ' counter(page);
				font: 8pt 'Hanken Grotesk', Arial, sans-serif;
				color: #000;
			}
		}
	</style>`}
</svelte:head>

{#if !loaded}
	<p class="status">Loading report…</p>
{:else if !assessment}
	<div class="status">
		<p>Assessment “{id}” was not found.</p>
		<a href="/history">Go to history</a>
	</div>
{:else}
	<div class="toolbar">
		<a href="/a/{id}">Back to assessment</a>
		<button type="button" onclick={() => window.print()}>Print / Save as PDF</button>
	</div>
	<main class="report">
		<Cover {assessment} />
		<Profile profile={assessment.profile} />
		<Regulations regulations={assessment.regulations} />
		<section>
			<h2>Requirements</h2>
			{#each groups as g (g.regulation)}
				<RequirementGroup {...g} />
			{/each}
		</section>
	</main>
{/if}

<style>
:global(body) {
	background: rgb(0 0 0 / 0.04);
	font-family: var(--font-grotesk);
	font-feature-settings: "ss01";
	color: black;
}
.status {
	max-width: 40rem;
	margin: 4rem auto;
	padding: 0 1rem;
	font-size: 1.5rem;
	font-weight: 300;
	line-height: 1.2;
}
.status a {
	font-size: 0.875rem;
	font-weight: 700;
	text-decoration: underline;
}
.toolbar {
	position: sticky;
	top: 0;
	z-index: 10;
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding: 0.75rem 2rem;
	background: white;
	border-bottom: 1px solid black;
	font-size: 0.875rem;
	font-weight: 500;
}
.toolbar a {
	text-decoration: underline;
	text-underline-offset: 2px;
}
.toolbar a:hover {
	color: var(--color-cv-teal-700);
}
.toolbar button {
	height: 2.25rem;
	padding: 0 0.75rem;
	background: black;
	color: white;
	font-weight: 700;
	border-radius: var(--radius-button);
	cursor: pointer;
}
.toolbar button:hover {
	background: var(--color-cv-ink-800);
}
.report {
	max-width: 210mm;
	margin: 1.5rem auto 3rem;
	padding: 18mm 16mm;
	background: white;
	border-radius: var(--radius-panel);
	font-size: 10pt;
	line-height: 1.4;
	color: black;
	counter-reset: section;
}
.report :global(h2) {
	counter-increment: section;
	display: grid;
	grid-template-columns: 30mm 1fr;
	align-items: end;
	margin-top: 9mm;
	margin-bottom: 3mm;
	padding-top: 2mm;
	border-top: 0.75pt solid black;
	font-size: 12pt;
	font-weight: 700;
	break-after: avoid;
}
.report :global(h2)::before {
	content: counter(section);
	font-size: 28pt;
	font-weight: 300;
	line-height: 0.85;
	color: var(--color-cv-teal-700);
}
.report :global(table) {
	width: 100%;
	border-collapse: collapse;
}
.report :global(a) {
	color: inherit;
}

@media print {
	:global(body) {
		background: white;
	}
	.toolbar {
		display: none;
	}
	.report {
		max-width: none;
		margin: 0;
		padding: 0;
	}
	.report :global(a) {
		text-decoration: none;
	}
}
</style>
