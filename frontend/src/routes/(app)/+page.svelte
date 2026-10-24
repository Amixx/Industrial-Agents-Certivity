<script lang="ts">
import { api } from '#lib/api/client.ts';
import exampleImage from '#lib/api/fixtures/exploded_view.png';
import exampleSpec from '#lib/api/fixtures/spec.md?raw';
import type { PipelineEvent } from '#lib/api/types.ts';
import Markdown from '#lib/components/Markdown.svelte';
import PipelineProgress from '#lib/components/PipelineProgress.svelte';
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
let view: 'edit' | 'preview' = $state('edit');
let events: PipelineEvent[] = $state([]);

async function setSpecFile(file: File | null | undefined) {
	if (!file) return;
	error = '';
	pdfNote = '';
	if (/\.pdf$|^application\/pdf$/i.test(file.type || file.name)) {
		try {
			const { text, pages } = await extractPdfText(file);
			spec = text;
			pdfNote = `Imported from ${file.name} · ${pages} page${pages === 1 ? '' : 's'}`;
		} catch (err) {
			error = err instanceof Error ? err.message : String(err);
			return;
		}
	} else {
		spec = await file.text();
	}
	specName = file.name;
	caseName = file.name.replace(/\.(md|txt|pdf)$/i, '');
	view = 'edit';
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

<svelte:head><title>New assessment · sudo</title></svelte:head>

{#if running}
	<div class="ui-rule flex items-baseline justify-between border-b px-4 py-2">
		<span class="ui-label opacity-100">Running assessment</span>
		<span class="ui-mono text-xs opacity-70">{caseName ?? 'untitled spec'}</span>
	</div>
	<PipelineProgress {events} />
{:else}
	<form
		class="grid min-h-0 flex-1 grid-cols-[1fr_20rem]"
		onsubmit={(e) => {
			e.preventDefault();
			run();
		}}
	>
		<label
			class="ui-rule flex min-h-0 flex-col border-r"
			ondragover={(e) => {
				e.preventDefault();
				dragging = true;
			}}
			ondragleave={() => (dragging = false)}
			ondrop={onDrop}
		>
			<div class="ui-rule flex items-baseline justify-between border-b px-3 py-1.5">
				<span class="ui-label font-medium opacity-100">
					Product spec <span class="ui-mono opacity-60">{specName || 'markdown'}</span>
				</span>
				<div class="flex">
					{#each ['edit', 'preview'] as const as v (v)}
						<button
							type="button"
							class="ui-tag h-6 cursor-pointer px-2 capitalize {v === 'preview'
								? '-ml-px'
								: ''} {view === v ? 'bg-cv-ink-800 text-cv-mint-50' : 'hover:bg-white'}"
							onclick={() => (view = v)}
						>
							{v}
						</button>
					{/each}
				</div>
			</div>
			{#if pdfNote}
				<div class="ui-rule-soft ui-mono border-b px-3 py-1 text-[11px]">
					{pdfNote}
					— review and edit before running
				</div>
			{/if}
			{#if view === 'preview'}
				<div class="min-h-0 flex-1 overflow-auto bg-white p-4">
					{#if spec.trim()}
						<Markdown source={spec} class="mx-auto max-w-3xl" />
					{:else}
						<p class="text-xs opacity-50">Nothing to preview yet.</p>
					{/if}
				</div>
			{:else}
				<textarea
					bind:value={spec}
					placeholder={'# spec: Product name\n\n## Product Type\n…\n\n## Vehicle Category\n…\n\n## Function\n- …\n\n## Main Parts\n- …\n\n## Materials\n| Component | Material |'}
					class="ui-mono min-h-0 flex-1 resize-none p-3 text-xs leading-relaxed outline-none {dragging
						? 'bg-cv-mint-300/30'
						: 'bg-white'}"
				></textarea>
			{/if}
		</label>

		<aside class="flex min-h-0 flex-col">
			<div class="ui-rule space-y-2 border-b p-3">
				<div class="ui-label">Spec file <span class="normal-case">(.md, .txt, .pdf)</span></div>
				<input
					type="file"
					accept=".md,.txt,.pdf,text/*,application/pdf"
					onchange={(e) => setSpecFile(e.currentTarget.files?.[0])}
					class="block w-full text-xs file:mr-2 file:border file:border-cv-ink-800 file:bg-white file:px-2 file:py-0.5"
				>
				<button type="button" class="ui-btn w-full" onclick={loadExample}>
					Load example: rear lamp
				</button>
				<button type="button" class="ui-btn w-full" onclick={loadExamplePdf}>Example PDF</button>
			</div>

			<div class="ui-rule flex min-h-0 flex-1 flex-col border-b p-3">
				<div class="mb-2 flex items-baseline justify-between">
					<span class="ui-label">Exploded view <span class="normal-case">(optional)</span></span>
					{#if imageUrl}
						<button type="button" class="ui-link text-[11px]" onclick={() => setImage(null)}>
							remove
						</button>
					{/if}
				</div>
				<div class="ui-rule flex min-h-32 flex-1 items-center justify-center border bg-white">
					{#if imageUrl}
						<img
							src={imageUrl}
							alt="Exploded view"
							class="max-h-full max-w-full object-contain p-2"
						>
					{:else}
						<span class="text-xs opacity-50">no image</span>
					{/if}
				</div>
				<input
					type="file"
					accept="image/*"
					onchange={(e) => setImage(e.currentTarget.files?.[0] ?? null)}
					class="mt-2 block w-full text-xs file:mr-2 file:border file:border-cv-ink-800 file:bg-white file:px-2 file:py-0.5"
				>
			</div>

			<div class="space-y-2 p-3">
				{#if error}
					<p class="ui-mono text-xs">ERROR {error}</p>
				{/if}
				<button class="ui-btn ui-btn-primary h-10 w-full" disabled={!spec.trim()}>
					Run assessment
				</button>
				<p class="text-[11px] leading-snug opacity-60">
					Finds the UN Regulations that apply, explains the ones it rules out, and cites every
					requirement to its page and paragraph.
				</p>
			</div>
		</aside>
	</form>
{/if}
