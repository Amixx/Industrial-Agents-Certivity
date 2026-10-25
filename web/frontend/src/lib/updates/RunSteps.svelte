<script lang="ts">
import { onDestroy } from 'svelte';
import type { UpdateRun } from '#lib/api/types.ts';

let {
	run,
	failed = null,
	label,
	ondone,
}: {
	/** The run once the backend returns it; null while the engine is working. */
	run: UpdateRun | null;
	/** The refusal or error, and the step it stops at. */
	failed?: { message: string; step: number } | null;
	/** What is being compared, shown on the first step until the run identifies it. */
	label: string;
	ondone: () => void;
} = $props();

/** How long each step stays on screen once its numbers are known, so they can be read. */
const STEP_MS = 320;

const steps = [
	'Identify regulation',
	'Parse both versions',
	'Align paragraphs',
	'Map requirements',
	'Done',
];

let reached = $state(0);
const timer = setInterval(() => {
	if (failed) return clearInterval(timer);
	// Step 1 can finish before the run returns; the rest need its numbers.
	if (reached >= 1 && !run) return;
	reached++;
	if (reached >= steps.length) {
		clearInterval(timer);
		setTimeout(ondone, STEP_MS);
	}
}, STEP_MS);
onDestroy(() => clearInterval(timer));

const pct = (x: number) => `${(x * 100).toFixed(1)}%`;
const sec = (x: number) => `${x.toFixed(2)} s`;

const notes = $derived.by(() => {
	if (!run) return [label, '', '', '', ''];
	const s = run.stats;
	const kinds = (k: string) => run.changes.filter((c) => c.change === k).length;
	const how = {
		sha256: 'matched by SHA-256 in the corpus',
		'first page': 'read from the first page',
		corpus: 'from the corpus',
	}[run.identifiedBy];
	return [
		`${run.regulation} ${run.toVersion}, ${how}`,
		`${s.oldParagraphs} paragraphs in ${run.fromVersion}, ${s.newParagraphs} in ${run.toVersion}, ${sec(s.seconds.parse)}`,
		`${s.oldUnits} sentences, ${pct(s.unchangedShare)} unchanged. ${s.amended} amended, ${s.new} new, ${s.deleted} deleted, ${sec(s.seconds.align)}`,
		`${s.requirements} requirements: ${kinds('modified')} modified, ${kinds('removed')} removed, ${kinds('added')} added`,
		`${run.fromVersion} to ${run.toVersion}, compared in ${sec(s.seconds.parse + s.seconds.align + s.seconds.map)}`,
	];
});
</script>

<ol class="border-t-2 border-line-strong">
	{#each steps as step, i (step)}
		{@const state = failed
			? i === failed.step
				? 'failed'
				: i < failed.step
					? 'done'
					: 'pending'
			: i < reached
				? 'done'
				: i === reached
					? 'active'
					: 'pending'}
		<li
			class="grid grid-cols-[2.5rem_1fr] border-b py-3 {state === 'active'
				? 'ui-row-selected border-line'
				: 'ui-rule-soft'}"
			class:opacity-30={state === 'pending'}
			style:--ui-marker-top="1.125rem"
		>
			<span class="pl-5 text-2xl leading-none font-light text-accent tabular-nums">{i + 1}</span>
			<div class="pl-2">
				<div class="font-bold">
					{step}
					{#if state === 'done' && i < steps.length - 1}
						<span class="font-normal text-accent">done</span>
					{/if}
				</div>
				{#if state === 'failed'}
					<p class="mt-1 text-sm">{failed?.message}</p>
				{:else if (state === 'done' || (i === steps.length - 1 && state !== 'pending')) && notes[i]}
					<p class="mt-1 font-mono text-[12px] text-muted tabular-nums">{notes[i]}</p>
				{:else if state === 'active' && i === 0}
					<p class="mt-1 font-mono text-[12px] text-muted">{label}</p>
				{/if}
			</div>
		</li>
	{/each}
</ol>
