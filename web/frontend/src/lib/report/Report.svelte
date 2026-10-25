<script lang="ts">
import type { Assessment } from '#lib/api/types.ts';
import Ask from './Ask.svelte';
import Brief from './Brief.svelte';
import Cover from './Cover.svelte';
import Profile from './Profile.svelte';
import Regulations from './Regulations.svelte';
import RequirementGroup from './RequirementGroup.svelte';
import RunCost from './RunCost.svelte';

let { assessment, inApp = false }: { assessment: Assessment; inApp?: boolean } = $props();

const sourceHref = $derived(inApp ? (id: string) => `/a/${assessment.id}?req=${id}` : undefined);

const groups = $derived.by(() => {
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
</script>

<main class="report">
	<Cover {assessment} />
	<Profile profile={assessment.profile} />
	<Regulations regulations={assessment.regulations} />
	{#if assessment.cost}
		<RunCost cost={assessment.cost} />
	{/if}
	<Brief requirements={assessment.requirements} {sourceHref} />
	<section>
		<h2>Requirements</h2>
		{#each groups as g (g.regulation)}
			<RequirementGroup {...g} />
		{/each}
	</section>
</main>
<Ask requirements={assessment.requirements} citeHref={sourceHref} />

<style>
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
