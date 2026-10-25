<script lang="ts">
import { onMount } from 'svelte';
import { api } from '#lib/api/client.ts';
import type { Assessment } from '#lib/api/types.ts';
import Report from '#lib/report/Report.svelte';
import { page } from '$app/state';

const id = $derived(page.params.id ?? '');

let assessment = $state<Assessment | null>(null);
let loaded = $state(false);

onMount(async () => {
	assessment = await api.getAssessment(id);
	loaded = true;
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
		<a href="/a/{id}/report">Back to assessment</a>
		<button type="button" onclick={() => window.print()}>Print / Save as PDF</button>
	</div>
	<Report {assessment} />
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

@media print {
	:global(body) {
		background: white;
	}
	.toolbar {
		display: none;
	}
}
</style>
