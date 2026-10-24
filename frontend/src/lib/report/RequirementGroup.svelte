<script lang="ts">
	import type { Requirement } from '#lib/api/types.ts';
	import { pdfHref } from './pdf.ts';

	let {
		regulation,
		title,
		requirements
	}: { regulation: string; title: string; requirements: Requirement[] } = $props();
</script>

<section class="group">
	<h3>{regulation} <span>{title}</span></h3>
	{#each requirements as req (req.id)}
		{@const href = pdfHref(req.source)}
		<article>
			<p class="id">{req.id}</p>
			<p class="text">{req.text}</p>
			<p class="cite">
				{req.source.regulation}, version {req.source.version} ·
				{#if href}
					<a {href} target="_blank" rel="noreferrer">page {req.source.page}</a>
				{:else}
					page {req.source.page}
				{/if}
				· § {req.source.paragraph}
			</p>
			<div class="review">
				<span class="verified"><span class="box"></span> Verified</span>
				<span class="notes">Notes:</span>
			</div>
		</article>
	{/each}
</section>

<style>
	.group {
		margin-top: 1.4rem;
	}
	h3 {
		font-size: 13pt;
		font-weight: 700;
		color: var(--color-cv-ink-800);
		border-bottom: 1pt solid var(--color-cv-ink-800);
		padding-bottom: 0.2rem;
		break-after: avoid;
	}
	h3 span {
		font-weight: 400;
		color: var(--color-cv-teal-700);
		font-size: 10.5pt;
		margin-left: 0.4rem;
	}
	article {
		break-inside: avoid;
		padding: 0.6rem 0;
		border-bottom: 0.5pt solid color-mix(in srgb, var(--color-cv-ink-800) 35%, white);
	}
	.id {
		font-family: ui-monospace, monospace;
		font-size: 8.5pt;
		font-weight: 600;
		color: var(--color-cv-teal-700);
	}
	.text {
		margin-top: 0.1rem;
	}
	.cite {
		margin-top: 0.25rem;
		font-size: 9pt;
		color: var(--color-cv-ink-800);
	}
	.cite a {
		text-decoration: underline;
		text-decoration-color: var(--color-cv-teal-500);
		text-underline-offset: 2px;
	}
	.review {
		display: flex;
		align-items: flex-end;
		gap: 1.2rem;
		margin-top: 0.55rem;
		font-size: 9pt;
		color: var(--color-cv-ink-800);
	}
	.verified {
		display: inline-flex;
		align-items: center;
		gap: 0.35rem;
		white-space: nowrap;
	}
	.box {
		width: 0.8rem;
		height: 0.8rem;
		border: 1pt solid var(--color-cv-ink-800);
	}
	.notes {
		flex: 1;
		border-bottom: 0.5pt solid var(--color-cv-ink-800);
		height: 1.1rem;
		line-height: 1;
		padding-top: 0.2rem;
	}
</style>
