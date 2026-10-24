<script lang="ts">
import { regulationIndex } from '#lib/api/regulations.ts';
import type { PipelineEvent, PipelineStep } from '#lib/api/types.ts';

let { events }: { events: PipelineEvent[] } = $props();

const steps: { step: PipelineStep; label: string }[] = [
	{ step: 'profile', label: 'Product profile' },
	{ step: 'selection', label: 'Regulation selection' },
	{ step: 'paragraphs', label: 'Paragraph scan' },
	{ step: 'requirements', label: 'Requirement extraction' },
	{ step: 'done', label: 'Assessment ready' },
];

const last = $derived(events.at(-1));
const partial = $derived(last?.partial);
const currentIndex = $derived(steps.findIndex((s) => s.step === last?.step));
const included = $derived(partial?.regulations?.filter((r) => r.included) ?? []);
const excluded = $derived(partial?.regulations?.filter((r) => !r.included) ?? []);

const stats = $derived([
	{ label: 'Parts', value: partial?.profile?.parts.length },
	{
		label: 'Regulations',
		value: partial?.regulations ? included.length : undefined,
		note: partial?.regulations ? `of ${regulationIndex.length} · ${excluded.length} excluded` : '',
	},
	{ label: 'Paragraphs', value: partial?.paragraphCount },
	{ label: 'Requirements', value: partial?.requirements?.length },
] as { label: string; value?: number; note?: string }[]);

function latestMessage(step: PipelineStep) {
	return events.findLast((e) => e.step === step)?.message;
}
</script>

<div class="grid min-h-0 flex-1 grid-cols-[22rem_1fr]">
	<ol class="ui-rule border-r">
		{#each steps as s, i (s.step)}
			{@const state =
				i < currentIndex || last?.step === 'done'
					? 'done'
					: i === currentIndex
						? 'active'
						: 'pending'}
			<li class="ui-rule-soft border-b px-4 py-3" class:opacity-40={state === 'pending'}>
				<div class="flex items-baseline gap-3">
					<span class="ui-mono w-5 text-xs"
						>{state === 'done' ? '✓' : state === 'active' ? '▸' : i + 1}</span
					>
					<span class="font-medium">{s.label}</span>
				</div>
				{#if latestMessage(s.step)}
					<p class="ui-mono mt-1 pl-8 text-[11px] opacity-80">{latestMessage(s.step)}</p>
				{/if}
			</li>
		{/each}
		<li class="px-4 py-3">
			<div class="ui-rule h-1.5 border">
				<div
					class="h-full bg-cv-teal-500 transition-[width] duration-300"
					style:width="{(last?.progress ?? 0) * 100}%"
				></div>
			</div>
			<p class="ui-mono mt-1 text-right text-[11px]">{Math.round((last?.progress ?? 0) * 100)}%</p>
		</li>
	</ol>

	<div class="grid min-h-0 grid-cols-4 grid-rows-[auto_1fr]">
		{#each stats as stat (stat.label)}
			<div class="ui-rule border-r border-b px-4 py-3 last:border-r-0">
				<div class="ui-label">{stat.label}</div>
				<div class="ui-mono text-3xl">{stat.value ?? '—'}</div>
				{#if stat.note}
					<div class="ui-mono text-[11px] opacity-70">{stat.note}</div>
				{/if}
			</div>
		{/each}

		<div class="ui-rule col-span-2 min-h-0 overflow-auto border-r px-4 py-3">
			{#if partial?.profile}
				<div class="ui-label mb-1">Understood from spec</div>
				<p class="mb-2">{partial.profile.productType}</p>
				<p class="ui-mono mb-2 text-xs">{partial.profile.vehicleCategory}</p>
				<ul class="space-y-0.5 text-xs">
					{#each partial.profile.functions as f (f)}
						<li>— {f}</li>
					{/each}
				</ul>
			{/if}
			{#if included.length}
				<div class="ui-label mt-4 mb-1">Selected</div>
				<ul class="space-y-1 text-xs">
					{#each included as r (r.regulation)}
						<li><span class="ui-mono font-medium">{r.regulation}</span> {r.title}</li>
					{/each}
				</ul>
				<div class="ui-label mt-3 mb-1">Excluded ({excluded.length})</div>
				<p class="ui-mono text-[11px] opacity-70">
					{excluded.map((r) => r.regulation).join(' · ')}
				</p>
			{/if}
		</div>

		<div class="col-span-2 min-h-0 overflow-auto px-4 py-3">
			<div class="ui-label mb-1">Requirements found</div>
			<ul class="space-y-1 text-xs">
				{#each (partial?.requirements ?? []).slice(-40).reverse() as r (r.id)}
					<li class="truncate"><span class="ui-mono mr-2">{r.id}</span>{r.text}</li>
				{/each}
			</ul>
		</div>
	</div>
</div>
