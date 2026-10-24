<script lang="ts">
import type { Assessment } from '#lib/api/types.ts';

let { assessment }: { assessment: Assessment } = $props();

const applied = $derived(assessment.regulations.filter((r) => r.included));
const date = $derived(
	new Date(assessment.createdAt).toLocaleDateString('en-GB', {
		day: 'numeric',
		month: 'long',
		year: 'numeric',
	}),
);
</script>

<header class="cover">
	<div class="top">
		<h1 class="wordmark">sudo</h1>
		<div class="credit">
			<p class="kind">Compliance requirements report</p>
			<p>In collaboration with <strong>Certivity</strong></p>
		</div>
	</div>
	<p class="case">{assessment.caseName ?? assessment.profile.productType}</p>
	<dl class="meta">
		<div>
			<dt>Product type</dt>
			<dd>{assessment.profile.productType}</dd>
		</div>
		<div>
			<dt>Vehicle category</dt>
			<dd>{assessment.profile.vehicleCategory}</dd>
		</div>
		<div>
			<dt>Date</dt>
			<dd>{date}</dd>
		</div>
		<div>
			<dt>Assessment id</dt>
			<dd class="id">{assessment.id}</dd>
		</div>
	</dl>
	<dl class="counts">
		<div>
			<dd>{applied.length}</dd>
			<dt>Regulations applied</dt>
		</div>
		<div>
			<dd>{assessment.requirements.length}</dd>
			<dt>Requirements</dt>
		</div>
	</dl>
</header>

<style>
.cover {
	border-top: 6px solid black;
	padding-top: 4mm;
	margin-bottom: 4mm;
}
.top {
	display: grid;
	grid-template-columns: 1fr 62mm;
	align-items: end;
}
.wordmark {
	font-size: 76pt;
	line-height: 0.78;
	font-weight: 700;
	letter-spacing: -0.06em;
}
.credit {
	font-size: 8.5pt;
}
.kind {
	font-size: 12pt;
	font-weight: 500;
	line-height: 1.2;
	margin-bottom: 2mm;
}
.case {
	margin-top: 12mm;
	font-size: 22pt;
	line-height: 1.1;
	font-weight: 700;
	letter-spacing: -0.02em;
}
.meta,
.counts {
	display: grid;
	grid-template-columns: repeat(4, 1fr);
	gap: 0 5mm;
	margin-top: 6mm;
}
.meta > div,
.counts > div {
	border-top: 0.75pt solid black;
	padding-top: 1.5mm;
}
.counts > div {
	border-top-width: 1.5pt;
}
dt {
	font-size: 8pt;
	font-weight: 700;
}
dd {
	font-size: 9.5pt;
	line-height: 1.3;
}
.counts dd {
	font-size: 30pt;
	font-weight: 300;
	line-height: 1;
	color: var(--color-cv-teal-700);
	font-variant-numeric: tabular-nums;
}
.counts dt {
	margin-top: 1mm;
	font-weight: 400;
}
.id {
	word-break: break-all;
	font-variant-numeric: tabular-nums;
}
</style>
