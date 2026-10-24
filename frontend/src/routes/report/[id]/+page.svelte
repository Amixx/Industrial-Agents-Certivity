<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import { api } from '#lib/api/client.ts';
	import type { Assessment } from '#lib/api/types.ts';
	import Cover from '#lib/report/Cover.svelte';
	import Profile from '#lib/report/Profile.svelte';
	import Regulations from '#lib/report/Regulations.svelte';
	import RequirementGroup from '#lib/report/RequirementGroup.svelte';

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
			requirements
		}));
	});

	const caseLabel = $derived(assessment?.caseName ?? assessment?.profile.productType ?? '');
	const pageCaseCss = $derived(caseLabel.replace(/[^\p{L}\p{N} ._-]/gu, ''));
</script>

<svelte:head>
	<title>{assessment ? `sudo report · ${caseLabel}` : 'sudo report'}</title>
	{@html `<style>
		@page {
			size: A4;
			margin: 18mm 16mm 20mm;
			@bottom-center {
				content: 'sudo · ${pageCaseCss} · page ' counter(page);
				font: 8pt Georgia, serif;
				color: #11504b;
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
		<a href="/a/{id}">← Back to assessment</a>
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
		background: var(--color-cv-mint-50);
	}
	.status {
		max-width: 40rem;
		margin: 4rem auto;
		padding: 0 1rem;
		text-align: center;
		color: var(--color-cv-ink-800);
	}
	.status a {
		text-decoration: underline;
	}
	.toolbar {
		position: sticky;
		top: 0;
		z-index: 10;
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.7rem 1.5rem;
		background: var(--color-cv-ink-950);
		color: white;
		font-size: 0.9rem;
	}
	.toolbar a:hover {
		text-decoration: underline;
	}
	.toolbar button {
		background: var(--color-cv-teal-400);
		color: var(--color-cv-ink-950);
		font-weight: 600;
		padding: 0.45rem 1rem;
		border-radius: 0.3rem;
		cursor: pointer;
	}
	.report {
		max-width: 210mm;
		margin: 1.5rem auto 3rem;
		padding: 18mm 16mm;
		background: white;
		box-shadow: 0 2px 16px rgb(2 49 47 / 0.12);
		font-family: Georgia, 'Times New Roman', serif;
		font-size: 10.5pt;
		line-height: 1.45;
		color: var(--color-cv-ink-950);
	}
	.report :global(h2) {
		margin-top: 1.6rem;
		margin-bottom: 0.5rem;
		font-size: 14pt;
		font-weight: 700;
		color: var(--color-cv-ink-800);
		break-after: avoid;
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
			box-shadow: none;
		}
		.report :global(a) {
			text-decoration: none;
		}
	}
</style>
