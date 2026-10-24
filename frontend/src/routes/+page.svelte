<script lang="ts">
	import { onMount } from 'svelte';
	import { app } from '#lib/app.svelte.ts';

	onMount(() => app.init());
</script>

<main class="mx-auto max-w-6xl space-y-8 p-6 text-gray-900">
	<h1 class="text-2xl font-semibold">Requirements from product spec</h1>

	<form
		onsubmit={(e) => {
			e.preventDefault();
			app.submit();
		}}
		class="space-y-4"
	>
		<div class="flex flex-wrap items-center gap-4">
			<label class="text-sm">
				Load case
				<select
					value={app.selectedCase}
					onchange={(e) => app.loadCase(e.currentTarget.value)}
					class="ml-2 rounded border border-gray-300 px-2 py-1"
				>
					<option value="">—</option>
					{#each app.cases as c}<option value={c}>{c}</option>{/each}
				</select>
			</label>
			<label class="text-sm">
				Spec file (.md)
				<input
					type="file"
					accept=".md,.txt,text/*"
					onchange={(e) => app.setSpecFile(e.currentTarget.files?.[0])}
					class="ml-2"
				/>
			</label>
			<label class="text-sm">
				Image
				<input
					type="file"
					accept="image/*"
					onchange={(e) => app.setImageFile(e.currentTarget.files?.[0])}
					class="ml-2"
				/>
			</label>
		</div>

		<textarea
			bind:value={app.spec}
			rows="12"
			placeholder="Product spec"
			class="w-full rounded border border-gray-300 p-2 font-mono text-sm"
		></textarea>

		{#if app.imageUrl}
			<img src={app.imageUrl} alt="Exploded view" class="max-h-64 rounded border border-gray-200" />
		{/if}

		<button
			disabled={app.loading}
			class="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50"
		>
			{app.loading ? 'Running…' : 'Submit'}
		</button>
		{#if app.error}<p class="text-red-600">{app.error}</p>{/if}
	</form>

	{#if app.result}
		<section class="space-y-3">
			<div class="flex items-center justify-between">
				<h2 class="text-lg font-semibold">{app.result.requirements.length} requirements</h2>
				<button
					onclick={() => app.download()}
					class="rounded border border-gray-300 px-3 py-1 hover:bg-gray-100"
				>
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
					{#each app.result.requirements as req (req.id)}
						{@const url = app.pdfUrl(req.source)}
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
