<script lang="ts">
import { api } from '#lib/api/client.ts';
import exampleImage from '#lib/api/fixtures/exploded_view.png';
import exampleSpec from '#lib/api/fixtures/spec.md?raw';
import type { PipelineEvent } from '#lib/api/types.ts';
import PipelineProgress from '#lib/components/PipelineProgress.svelte';
import SpecEditor from '#lib/components/SpecEditor.svelte';
import { extractPdfText } from '#lib/spec/pdfText.ts';
import { goto } from '$app/navigation';

const EXAMPLE_CASE = 'dev-rear-lamp';

let spec = $state('');
let specName = $state('');
let caseName: string | undefined = $state();
let image: Blob | null = $state(null);
let imageUrl: string | null = $state(null);
let dragging = $state(false);
let running = $state(false);
let error = $state('');
let pdfNote = $state('');
let events: PipelineEvent[] = $state([]);

async function setSpecFile(file: File | null | undefined) {
	if (!file) return;
	error = '';
	pdfNote = '';
	if (/\.pdf$|^application\/pdf$/i.test(file.type || file.name)) {
		try {
			const { text, pages } = await extractPdfText(file);
			spec = text;
			pdfNote = `Imported from ${file.name}, ${pages} page${pages === 1 ? '' : 's'}.`;
		} catch (err) {
			error = err instanceof Error ? err.message : String(err);
			return;
		}
	} else {
		spec = await file.text();
	}
	specName = file.name;
	caseName = file.name.replace(/\.(md|txt|pdf)$/i, '');
}

async function loadExamplePdf() {
	error = '';
	const blob = await fetch('/examples/rear-lamp-spec.pdf').then((r) => r.blob());
	await setSpecFile(new File([blob], 'rear-lamp-spec.pdf', { type: 'application/pdf' }));
	caseName = EXAMPLE_CASE;
}

function setImage(blob: Blob | null) {
	if (imageUrl?.startsWith('blob:')) URL.revokeObjectURL(imageUrl);
	image = blob;
	imageUrl = blob ? URL.createObjectURL(blob) : null;
}

async function loadExample() {
	error = '';
	pdfNote = '';
	try {
		const data = await fetch(`/api/cases/${EXAMPLE_CASE}`).then((r) => {
			if (!r.ok) throw new Error();
			return r.json();
		});
		spec = data.spec;
		setImage(data.image_url ? await fetch(data.image_url).then((r) => r.blob()) : null);
	} catch {
		spec = exampleSpec;
		setImage(await fetch(exampleImage).then((r) => r.blob()));
	}
	specName = 'spec.md';
	caseName = EXAMPLE_CASE;
}

async function run() {
	running = true;
	error = '';
	events = [];
	try {
		const assessment = await api.runAssessment(spec, image, (e) => events.push(e), caseName);
		await new Promise((r) => setTimeout(r, 600));
		await goto(`/a/${assessment.id}`);
	} catch (err) {
		error = String(err);
		running = false;
	}
}

function onDrop(e: DragEvent) {
	e.preventDefault();
	dragging = false;
	for (const file of e.dataTransfer?.files ?? []) {
		if (file.type.startsWith('image/')) setImage(file);
		else setSpecFile(file);
	}
}
</script>

<svelte:head><title>New assessment | sudo</title></svelte:head>

{#if running}
	<div class="ui-grid min-h-0 flex-1 pb-6">
		<div class="col-span-2">
			<span class="ui-label">Step 02</span>
			<h1 class="ui-display mt-3 text-[2.5rem]">Running <i>assessment</i></h1>
			<div class="mt-3 font-mono text-xs text-muted">{caseName ?? 'Untitled spec'}</div>
		</div>
		<PipelineProgress {events} class="col-span-10" />
	</div>
{:else}
	<form
		class="ui-grid min-h-0 flex-1 pb-6"
		onsubmit={(e) => {
			e.preventDefault();
			run();
		}}
	>
		<div class="col-span-2">
			<span class="ui-label">Step 01</span>
			<h1 class="ui-display mt-3 text-[2.5rem]">New <i>assessment</i></h1>
			<p class="mt-4 max-w-[26ch] text-xs leading-relaxed text-muted">
				Finds the UN Regulations that apply, explains the ones it rules out, and cites every
				requirement to its page and paragraph.
			</p>
		</div>

		<section
			aria-label="Product spec"
			class="ui-panel col-span-7 flex min-h-0 flex-col {dragging ? 'border-accent' : ''}"
			ondragover={(e) => {
				e.preventDefault();
				dragging = true;
			}}
			ondragleave={() => (dragging = false)}
			ondrop={onDrop}
		>
			<div class="flex items-baseline justify-between border-b border-line px-4 py-2.5">
				<span class="ui-label">Product spec</span>
				<span class="font-mono text-[11px] text-faint">{specName || 'Markdown'}</span>
			</div>
			{#if pdfNote}
				<p class="border-b border-line bg-select px-4 py-1.5 text-xs">
					{pdfNote}
					Review and edit before running.
				</p>
			{/if}
			<SpecEditor
				bind:value={spec}
				placeholder="Paste or drop a product spec. Click any line to edit it."
				class="min-h-0 flex-1 overflow-auto px-2 py-3"
			/>
		</section>

		<aside class="col-span-3 flex min-h-0 flex-col gap-7">
			<div class="flex flex-col gap-2">
				<span class="ui-label mb-1">Spec</span>
				<label class="block">
					<span class="sr-only">Spec file, .md, .txt or .pdf</span>
					<input
						type="file"
						accept=".md,.txt,.pdf,text/*,application/pdf"
						onchange={(e) => setSpecFile(e.currentTarget.files?.[0])}
						class="ui-file"
					>
				</label>
				<button type="button" class="ui-btn w-full" onclick={loadExample}>
					Load example: rear lamp
				</button>
				<button type="button" class="ui-btn w-full" onclick={loadExamplePdf}>Example PDF</button>
			</div>

			<div class="flex min-h-0 flex-1 flex-col">
				<div class="mb-2 flex items-baseline justify-between">
					<span class="ui-label">Exploded view, optional</span>
					{#if imageUrl}
						<button type="button" class="ui-link text-xs" onclick={() => setImage(null)}>
							Remove
						</button>
					{/if}
				</div>
				<div
					class="flex min-h-32 flex-1 items-center justify-center rounded-panel border border-dashed border-line-strong"
				>
					{#if imageUrl}
						<img
							src={imageUrl}
							alt="Exploded view"
							class="max-h-full max-w-full rounded-control bg-white object-contain p-2"
						>
					{:else}
						<span class="text-xs text-faint">No drawing</span>
					{/if}
				</div>
				<input
					type="file"
					accept="image/*"
					onchange={(e) => setImage(e.currentTarget.files?.[0] ?? null)}
					class="ui-file mt-2"
				>
			</div>

			<div class="flex flex-col gap-2">
				{#if error}
					<p class="border-l-2 border-red-400 pl-2 text-xs text-red-300">{error}</p>
				{/if}
				<button type="submit" class="ui-btn ui-btn-primary h-10 w-full" disabled={!spec.trim()}>
					Run assessment
				</button>
			</div>
		</aside>
	</form>
{/if}
