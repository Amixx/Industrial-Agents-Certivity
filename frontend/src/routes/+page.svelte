<script lang="ts">
	import { onMount } from 'svelte';

	type Requirement = {
		id: string;
		text: string;
		source: { regulation: string; version: string; page: number; paragraph?: string };
	};
	type Regulation = {
		regulation: string;
		versions: { role: string; version_label: string; files: { name: string }[] }[];
	};

	let cases: string[] = $state([]);
	let regulations: Regulation[] = $state([]);
	let selectedCase = $state('');
	let spec = $state('');
	let image: File | null = $state(null);
	let imageUrl: string | null = $state(null);
	let loading = $state(false);
	let error = $state('');
	let result: { requirements: Requirement[] } | null = $state(null);

	onMount(async () => {
		[cases, regulations] = await Promise.all([
			fetch('/api/cases').then((r) => r.json()),
			fetch('/api/regulations').then((r) => r.json())
		]);
	});

	async function loadCase() {
		if (!selectedCase) return;
		const data = await fetch(`/api/cases/${selectedCase}`).then((r) => r.json());
		spec = data.spec;
		imageUrl = data.image_url;
		image = null;
	}

	async function onSpecFile(e: Event) {
		const file = (e.target as HTMLInputElement).files?.[0];
		if (file) spec = await file.text();
	}

	function onImageFile(e: Event) {
		image = (e.target as HTMLInputElement).files?.[0] ?? null;
		imageUrl = image ? URL.createObjectURL(image) : null;
	}

	async function submit(e: Event) {
		e.preventDefault();
		loading = true;
		error = '';
		try {
			const body = new FormData();
			body.set('spec', spec);
			if (image) body.set('image', image);
			else if (imageUrl && selectedCase) {
				const blob = await fetch(imageUrl).then((r) => r.blob());
				body.set('image', blob, 'exploded_view.png');
			}
			const res = await fetch('/api/requirements', { method: 'POST', body });
			if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
			result = await res.json();
		} catch (err) {
			error = String(err);
		} finally {
			loading = false;
		}
	}

	function pdfUrl({ regulation, version, page }: Requirement['source']) {
		const entry = regulations.find((r) => r.regulation === regulation);
		const v = entry?.versions.find((v) => v.version_label === version);
		if (!entry || !v) return null;
		const dir = regulation.replace(' ', '_');
		return `/pdfs/${dir}/${v.role}/${v.files[0].name}#page=${page}`;
	}

	function download() {
		const blob = new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' });
		const a = document.createElement('a');
		a.href = URL.createObjectURL(blob);
		a.download = 'requirements.json';
		a.click();
		URL.revokeObjectURL(a.href);
	}
</script>

<main class="mx-auto max-w-6xl space-y-8 p-6 text-gray-900">
	<h1 class="text-2xl font-semibold">Requirements from product spec</h1>

	<form onsubmit={submit} class="space-y-4">
		<div class="flex flex-wrap items-center gap-4">
			<label class="text-sm">
				Load case
				<select
					bind:value={selectedCase}
					onchange={loadCase}
					class="ml-2 rounded border border-gray-300 px-2 py-1"
				>
					<option value="">—</option>
					{#each cases as c}<option value={c}>{c}</option>{/each}
				</select>
			</label>
			<label class="text-sm">
				Spec file (.md)
				<input type="file" accept=".md,.txt,text/*" onchange={onSpecFile} class="ml-2" />
			</label>
			<label class="text-sm">
				Image
				<input type="file" accept="image/*" onchange={onImageFile} class="ml-2" />
			</label>
		</div>

		<textarea
			bind:value={spec}
			rows="12"
			placeholder="Product spec"
			class="w-full rounded border border-gray-300 p-2 font-mono text-sm"
		></textarea>

		{#if imageUrl}
			<img src={imageUrl} alt="Exploded view" class="max-h-64 rounded border border-gray-200" />
		{/if}

		<button
			disabled={loading}
			class="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50"
		>
			{loading ? 'Running…' : 'Submit'}
		</button>
		{#if error}<p class="text-red-600">{error}</p>{/if}
	</form>

	{#if result}
		<section class="space-y-3">
			<div class="flex items-center justify-between">
				<h2 class="text-lg font-semibold">{result.requirements.length} requirements</h2>
				<button onclick={download} class="rounded border border-gray-300 px-3 py-1 hover:bg-gray-100">
					Download JSON
				</button>
			</div>
			<table class="w-full border-collapse text-left text-sm">
				<thead>
					<tr class="border-b border-gray-300 bg-gray-50">
						<th class="p-2">ID</th>
						<th class="p-2">Requirement</th>
						<th class="p-2">Regulation</th>
						<th class="p-2">Version</th>
						<th class="p-2">Page</th>
						<th class="p-2">Paragraph</th>
					</tr>
				</thead>
				<tbody>
					{#each result.requirements as req (req.id)}
						{@const url = pdfUrl(req.source)}
						<tr class="border-b border-gray-200 align-top">
							<td class="p-2 whitespace-nowrap">{req.id}</td>
							<td class="p-2">{req.text}</td>
							<td class="p-2 whitespace-nowrap">{req.source.regulation}</td>
							<td class="p-2 whitespace-nowrap">{req.source.version}</td>
							<td class="p-2">
								{#if url}
									<a href={url} target="_blank" rel="noreferrer" class="text-blue-600 underline">
										{req.source.page}
									</a>
								{:else}
									{req.source.page}
								{/if}
							</td>
							<td class="p-2 whitespace-nowrap">{req.source.paragraph ?? ''}</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</section>
	{/if}
</main>
