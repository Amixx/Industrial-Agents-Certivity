<script lang="ts">
import type { Requirement } from '#lib/api/types.ts';
import { pdfHref } from './pdf.ts';

let {
	regulation,
	title,
	requirements,
}: { regulation: string; title: string; requirements: Requirement[] } = $props();
</script>

<section class="group">
	<h3>
		<span class="reg">{regulation}</span>
		<span class="title">{title}</span>
		<span class="count">{requirements.length}</span>
	</h3>
	{#each requirements as req (req.id)}
		{@const href = pdfHref(req.source)}
		<article>
			<p class="para">{req.source.paragraph}</p>
			<div>
				<p class="text">{req.text}</p>
				<p class="cite">
					<span class="id">{req.id}</span>
					<span>{req.source.regulation}, version {req.source.version}</span>
					{#if href}
						<a {href} target="_blank" rel="noreferrer">Page {req.source.page}</a>
					{:else}
						<span>Page {req.source.page}</span>
					{/if}
					<span>§ {req.source.paragraph}</span>
				</p>
				<div class="review">
					<span class="verified"><span class="box"></span> Verified</span>
					<span class="notes">Notes</span>
				</div>
			</div>
		</article>
	{/each}
</section>

<style>
.group {
	margin-top: 6mm;
}
h3 {
	display: grid;
	grid-template-columns: 30mm 1fr auto;
	align-items: baseline;
	font-size: 10pt;
	border-bottom: 1.5pt solid black;
	padding-bottom: 1mm;
	break-after: avoid;
}
.reg {
	font-weight: 700;
}
.title {
	font-weight: 500;
}
.count {
	font-variant-numeric: tabular-nums;
}
article {
	display: grid;
	grid-template-columns: 30mm 1fr;
	break-inside: avoid;
	padding: 2.5mm 0;
	border-bottom: 0.5pt solid rgb(0 0 0 / 0.2);
}
.para {
	padding-right: 3mm;
	font-size: 14pt;
	font-weight: 300;
	line-height: 1;
	letter-spacing: -0.01em;
	color: var(--color-cv-teal-700);
	font-variant-numeric: tabular-nums;
	word-break: break-all;
}
.text {
	font-size: 10.5pt;
	line-height: 1.4;
}
.cite {
	display: flex;
	flex-wrap: wrap;
	gap: 0 4mm;
	margin-top: 1.5mm;
	font-size: 8.5pt;
}
.id {
	font-weight: 700;
}
.cite a {
	text-decoration: underline;
	text-underline-offset: 2px;
}
.review {
	display: flex;
	align-items: flex-end;
	gap: 5mm;
	margin-top: 2.5mm;
	font-size: 8.5pt;
}
.verified {
	display: inline-flex;
	align-items: center;
	gap: 1.5mm;
	white-space: nowrap;
}
.box {
	width: 3mm;
	height: 3mm;
	border: 0.75pt solid black;
	border-radius: var(--radius-control);
}
.notes {
	flex: 1;
	border-bottom: 0.5pt solid black;
	height: 4.5mm;
	line-height: 1;
	padding-top: 0.8mm;
}
</style>
