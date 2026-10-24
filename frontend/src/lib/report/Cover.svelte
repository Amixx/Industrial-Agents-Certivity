<script lang="ts">
	import type { Assessment } from '#lib/api/types.ts';

	let { assessment }: { assessment: Assessment } = $props();

	const applied = $derived(assessment.regulations.filter((r) => r.included));
	const date = $derived(
		new Date(assessment.createdAt).toLocaleDateString('en-GB', {
			day: 'numeric',
			month: 'long',
			year: 'numeric'
		})
	);
</script>

<header class="cover">
	<h1 class="wordmark">sudo</h1>
	<p class="subtitle">Compliance requirements report · prepared in collaboration with Certivity</p>
	<h2 class="case">{assessment.caseName ?? assessment.profile.productType}</h2>
	<dl class="meta">
		<div><dt>Product type</dt><dd>{assessment.profile.productType}</dd></div>
		<div><dt>Vehicle category</dt><dd>{assessment.profile.vehicleCategory}</dd></div>
		<div><dt>Date</dt><dd>{date}</dd></div>
		<div><dt>Assessment id</dt><dd class="mono">{assessment.id}</dd></div>
		<div><dt>Regulations applied</dt><dd>{applied.length}</dd></div>
		<div><dt>Requirements</dt><dd>{assessment.requirements.length}</dd></div>
	</dl>
</header>

<style>
	.cover {
		border-bottom: 2px solid var(--color-cv-ink-800);
		padding-bottom: 1.2rem;
		margin-bottom: 1.6rem;
	}
	.wordmark {
		font-size: 44pt;
		line-height: 1;
		font-weight: 700;
		letter-spacing: -0.03em;
		color: var(--color-cv-ink-950);
	}
	.subtitle {
		margin-top: 0.4rem;
		font-size: 10pt;
		color: var(--color-cv-teal-700);
	}
	.case {
		margin-top: 1.4rem;
		font-size: 18pt;
		font-weight: 600;
		color: var(--color-cv-ink-800);
	}
	.meta {
		margin-top: 0.9rem;
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 0.7rem 1.2rem;
	}
	dt {
		font-size: 8pt;
		text-transform: uppercase;
		letter-spacing: 0.06em;
		color: var(--color-cv-teal-700);
	}
	dd {
		font-size: 10.5pt;
	}
	.mono {
		font-family: ui-monospace, monospace;
		font-size: 9pt;
		word-break: break-all;
	}
</style>
