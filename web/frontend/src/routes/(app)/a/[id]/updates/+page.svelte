<script lang="ts">
import { api } from '#lib/api/client.ts';
import {
	type Assessment,
	type CitedRegulation,
	UpdateRefusal,
	type UpdateRequest,
	type UpdateRun,
} from '#lib/api/types.ts';
import AssessmentHeader from '#lib/components/AssessmentHeader.svelte';
import RunSteps from '#lib/updates/RunSteps.svelte';
import { goto } from '$app/navigation';
import type { PageProps } from './$types';

let { params }: PageProps = $props();

let assessment = $state<Assessment | null>(null);
let cited = $state<CitedRegulation[] | null>(null);

$effect(() => {
	const id = params.id;
	api.getAssessment(id).then((a) => (assessment = a));
	api.listUpdates(id).then((c) => (cited = c));
});

/** The comparison in progress: what it compares, and its run or refusal once known. */
let started = $state<{
	label: string;
	request: UpdateRequest;
	run: UpdateRun | null;
	failed: { message: string; step: number } | null;
	/** Set when the PDF is not in the corpus and its version must be entered. */
	needsVersion?: { regulation?: string; version?: string };
} | null>(null);
let version = $state('');
let dragging = $state(false);
let fileInput = $state<HTMLInputElement | null>(null);

async function start(request: UpdateRequest, label: string, toVersion?: string) {
	if (!assessment) return;
	started = { label, request, run: null, failed: null };
	try {
		const run = await api.createUpdate(assessment.id, request, toVersion);
		if (started) started.run = run;
	} catch (e) {
		if (!started) return;
		const refusal = e instanceof UpdateRefusal ? e : null;
		started.failed = {
			message: e instanceof Error ? e.message : String(e),
			step: refusal?.code === 'mismatch' ? 2 : 0,
		};
		if (refusal?.code === 'version_needed') {
			started.needsVersion = { regulation: refusal.regulation, version: refusal.version };
			version = refusal.version ?? '';
		}
	}
}

function upload(file: File | undefined) {
	if (file) start({ file }, file.name);
}

function onDrop(e: DragEvent) {
	e.preventDefault();
	dragging = false;
	upload(e.dataTransfer?.files[0]);
}

const pending = $derived(cited?.filter((c) => c.latest) ?? []);
</script>

<svelte:head><title>Updates | sudo</title></svelte:head>

{#if assessment}
	<AssessmentHeader {assessment} />
{/if}

<div class="min-h-0 flex-1 overflow-auto pt-6 pb-12">
	<div class="ui-grid">
		<div class="col-span-12 flex items-baseline gap-6 xl:col-span-8">
			<h1 class="ui-display text-5xl">Regulation <em class="text-accent">updates</em></h1>
			{#if cited}
				<p class="font-mono text-[12px] text-muted tabular-nums">
					{cited.length}
					cited, {pending.length} with a newer version in the corpus
				</p>
			{/if}
		</div>
	</div>

	<div class="ui-grid mt-6">
		<section
			class="ui-panel col-span-12 flex items-center gap-6 px-6 py-6 xl:col-span-8 {dragging
				? 'border-accent bg-select'
				: ''}"
			aria-label="Upload a new version"
			ondragover={(e) => {
				e.preventDefault();
				dragging = true;
			}}
			ondragleave={() => (dragging = false)}
			ondrop={onDrop}
		>
			<div class="min-w-0 flex-1">
				<p class="text-base font-bold">Upload a new version of a cited regulation</p>
				<p class="mt-1 text-xs text-muted">
					Drop the PDF here. It is compared paragraph by paragraph with the version this assessment
					cites, and every requirement it touches is listed.
				</p>
			</div>
			<input
				bind:this={fileInput}
				type="file"
				accept="application/pdf,.pdf"
				class="hidden"
				onchange={(e) => upload(e.currentTarget.files?.[0])}
			>
			<button type="button" class="ui-btn" onclick={() => fileInput?.click()}>Choose PDF</button>
		</section>
	</div>

	{#if started}
		<section class="ui-grid mt-8">
			<div class="col-span-12 xl:col-span-8">
				<div class="mb-3 flex items-baseline justify-between">
					<div class="ui-label">Comparing</div>
					{#if started.failed}
						<button type="button" class="ui-link text-xs" onclick={() => (started = null)}>
							Back to the list
						</button>
					{/if}
				</div>
				<RunSteps
					run={started.run}
					failed={started.failed}
					label={started.label}
					ondone={() => started?.run && goto(`/a/${params.id}/updates/${started.run.id}`)}
				/>
				{#if started.needsVersion}
					{@const request = started.request}
					<form
						class="mt-4 flex items-center gap-3"
						onsubmit={(e) => {
							e.preventDefault();
							if (version) start(request, started?.label ?? '', version.trim());
						}}
					>
						<label class="text-xs" for="version">
							Version of {started.needsVersion.regulation ?? 'this regulation'}
						</label>
						<input
							id="version"
							class="ui-input w-28 font-mono"
							bind:value={version}
							placeholder="1.7.0"
						>
						<button type="submit" class="ui-btn ui-btn-primary" disabled={!version}>Compare</button>
					</form>
				{/if}
			</div>
		</section>
	{:else}
		<section class="ui-grid mt-8">
			<div class="col-span-12 xl:col-span-8">
				<div class="ui-label mb-2">Cited regulations</div>
				<table class="w-full border-t-2 border-line-strong text-left">
					<thead>
						<tr
							class="ui-rule-soft border-b font-mono text-[11.5px] tracking-[0.08em] text-muted uppercase"
						>
							<th class="py-2 font-medium">Regulation</th>
							<th class="py-2 font-medium">Cited</th>
							<th class="py-2 font-medium">Latest in corpus</th>
							<th class="py-2 text-right font-medium">Requirements</th>
							<th class="py-2"></th>
						</tr>
					</thead>
					<tbody>
						{#each cited ?? [] as c (c.regulation)}
							<tr class="ui-rule-soft border-b">
								<td class="py-3 pr-4">
									<div class="font-bold">{c.regulation}</div>
									<div class="max-w-[46ch] truncate text-xs text-muted">{c.title}</div>
								</td>
								<td class="py-3 pr-4 font-mono tabular-nums">{c.version}</td>
								<td class="py-3 pr-4 font-mono tabular-nums">
									{#if c.latest}
										<span class="flex items-center gap-2">
											<span class="size-2 bg-mark"></span>{c.latest}
										</span>
									{:else}
										<span class="text-muted">{c.version}, up to date</span>
									{/if}
								</td>
								<td
									class="py-3 pr-6 text-right text-2xl leading-none font-light text-accent tabular-nums"
								>
									{c.requirementCount}
								</td>
								<td class="py-3 text-right">
									{#if c.latest}
										<button
											type="button"
											class="ui-btn"
											onclick={() =>
												start({ regulation: c.regulation }, `${c.regulation} ${c.latest}`)}
										>
											Compare with {c.latest}
										</button>
									{:else if c.appliedRun}
										<a href="/a/{params.id}/updates/{c.appliedRun}" class="ui-link text-xs">
											Applied, see the comparison
										</a>
									{/if}
								</td>
							</tr>
						{:else}
							<tr>
								<td colspan="5" class="py-3 text-sm text-muted">Loading the cited regulations.</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</section>
	{/if}
</div>
