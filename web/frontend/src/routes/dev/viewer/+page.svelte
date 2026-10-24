<script lang="ts">
import PdfViewer from '#lib/components/PdfViewer.svelte';

type Preset = {
	label: string;
	url: string;
	page: number;
	highlight: { paragraph?: string; text?: string } | null;
};

const presets: Preset[] = [
	{
		label: 'R150 p7 §3.3.1.1',
		url: '/pdfs/UN_R150/base/UN_R150_base.pdf',
		page: 7,
		highlight: { paragraph: '3.3.1.1' },
	},
	{
		label: 'R48 p61 §6.19.7.3',
		url: '/pdfs/UN_R48/base/UN_R48_base.pdf',
		page: 61,
		highlight: { paragraph: '6.19.7.3' },
	},
	{
		label: 'R150 p25 Annex 2 1.2',
		url: '/pdfs/UN_R150/base/UN_R150_base.pdf',
		page: 25,
		highlight: { paragraph: 'Annex 2 1.2' },
	},
	{
		label: 'R150 p7 text only',
		url: '/pdfs/UN_R150/base/UN_R150_base.pdf',
		page: 7,
		highlight: {
			text: 'The four to six-digit sequential number being part of the approval number prescribed in paragraph 3.2.3.2. shall be placed close to the approval mark.',
		},
	},
	{
		label: 'R48 p61 missing §9.9.9',
		url: '/pdfs/UN_R48/base/UN_R48_base.pdf',
		page: 61,
		highlight: { paragraph: '9.9.9' },
	},
];

let selected = $state(0);
const preset = $derived(presets[selected]);
</script>

<div class="flex h-screen flex-col gap-3 bg-cv-mint-50 p-4 text-cv-ink-950">
	<div class="flex flex-wrap gap-2">
		{#each presets as p, i (p.label)}
			<button
				type="button"
				data-preset={i}
				class="rounded border border-cv-teal-700 px-3 py-1 text-sm {i === selected
					? 'bg-cv-teal-700 text-white'
					: 'bg-white text-cv-teal-700'}"
				onclick={() => (selected = i)}
			>
				{p.label}
			</button>
		{/each}
	</div>
	<PdfViewer
		class="min-h-0 flex-1"
		url={preset.url}
		page={preset.page}
		highlight={preset.highlight}
	/>
</div>
