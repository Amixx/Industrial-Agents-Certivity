<script lang="ts">
	import { goto } from '$app/navigation';
	import { api } from '#lib/api/client.ts';
	import type { PipelineEvent } from '#lib/api/types.ts';
	import exampleSpec from '#lib/api/fixtures/spec.md?raw';
	import exampleImage from '#lib/api/fixtures/exploded_view.png';
	import PipelineProgress from '#lib/components/PipelineProgress.svelte';

	const EXAMPLE_CASE = 'dev-rear-lamp';

	let spec = $state('');
	let specName = $state('');
	let caseName: string | undefined = $state();
	let image: Blob | null = $state(null);
	let imageUrl: string | null = $state(null);
	let dragging = $state(false);
	let running = $state(false);
	let error = $state('');
	let events: PipelineEvent[] = $state([]);

	async function setSpecFile(file: File | null | undefined) {
		if (!file) return;
		spec = await file.text();
		specName = file.name;
		caseName = file.name.replace(/\.(md|txt)$/i, '');
	}

	function setImage(blob: Blob | null) {
		if (imageUrl?.startsWith('blob:')) URL.revokeObjectURL(imageUrl);
		image = blob;
		imageUrl = blob ? URL.createObjectURL(blob) : null;
	}

	async function loadExample() {
		error = '';
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
				<span class="text-[11px] opacity-60">Paste, or drop a .md file and an image anywhere here</span>
			</div>
			<textarea
				bind:value={spec}
				placeholder={'# spec: Product name\n\n## Product Type\n…\n\n## Vehicle Category\n…\n\n## Function\n- …\n\n## Main Parts\n- …\n\n## Materials\n| Component | Material |'}
				class="ui-mono min-h-0 flex-1 resize-none p-3 text-xs leading-relaxed outline-none {dragging
					? 'bg-cv-mint-300/30'
					: 'bg-white'}"
			></textarea>
		</label>

		<aside class="flex min-h-0 flex-col">
			<div class="ui-rule space-y-2 border-b p-3">
				<div class="ui-label">Spec file</div>
				<input
					type="file"
					accept=".md,.txt,text/*"
					onchange={(e) => setSpecFile(e.currentTarget.files?.[0])}
					class="block w-full text-xs file:mr-2 file:border file:border-cv-ink-800 file:bg-white file:px-2 file:py-0.5"
				/>
				<button type="button" class="ui-btn w-full" onclick={loadExample}>Load example: rear lamp</button>
			</div>

			<div class="ui-rule flex min-h-0 flex-1 flex-col border-b p-3">
				<div class="mb-2 flex items-baseline justify-between">
					<span class="ui-label">Exploded view <span class="normal-case">(optional)</span></span>
					{#if imageUrl}
						<button type="button" class="ui-link text-[11px]" onclick={() => setImage(null)}>remove</button>
					{/if}
				</div>
				<div class="ui-rule flex min-h-32 flex-1 items-center justify-center border bg-white">
					{#if imageUrl}
						<img src={imageUrl} alt="Exploded view" class="max-h-full max-w-full object-contain p-2" />
					{:else}
						<span class="text-xs opacity-50">no image</span>
					{/if}
				</div>
				<input
					type="file"
					accept="image/*"
					onchange={(e) => setImage(e.currentTarget.files?.[0] ?? null)}
					class="mt-2 block w-full text-xs file:mr-2 file:border file:border-cv-ink-800 file:bg-white file:px-2 file:py-0.5"
				/>
			</div>

			<div class="space-y-2 p-3">
				{#if error}<p class="ui-mono text-xs">ERROR {error}</p>{/if}
				<button class="ui-btn ui-btn-primary h-10 w-full" disabled={!spec.trim()}>Run assessment</button>
				<p class="text-[11px] leading-snug opacity-60">
					Finds the UN Regulations that apply, explains the ones it rules out, and cites every requirement to
					its page and paragraph.
				</p>
			</div>
		</aside>
	</form>
{/if}
