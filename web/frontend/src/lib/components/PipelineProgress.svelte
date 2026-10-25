<script lang="ts">
import { regulationIndex } from '#lib/api/regulations.ts';
import type { PipelineEvent, PipelineStep } from '#lib/api/types.ts';

let { events, class: klass = '' }: { events: PipelineEvent[]; class?: string } = $props();

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
		notes: partial?.regulations
			? [`of ${regulationIndex.length} considered`, `${excluded.length} excluded`]
			: [],
	},
	{ label: 'Paragraphs', value: partial?.paragraphCount },
	{ label: 'Requirements', value: partial?.requirements?.length },
] as { label: string; value?: number; notes?: string[] }[]);

function latestMessage(step: PipelineStep) {
	return events.findLast((e) => e.step === step)?.message;
}
</script>

<div class="grid min-h-0 grid-cols-10 gap-x-4 xl:gap-x-6 {klass}">
	<ol class="col-span-3 flex min-h-0 flex-col overflow-auto">
		{#each steps as s, i (s.step)}
			{@const state =
				i < currentIndex || last?.step === 'done'
					? 'done'
					: i === currentIndex
						? 'active'
						: 'pending'}
			<li
				class="grid grid-cols-[2.5rem_1fr] border-b py-3 {i === 0
					? 'border-t-2 border-t-line-strong'
					: ''} {state === 'active' ? 'ui-row-selected border-line' : 'ui-rule-soft'}"
				class:opacity-30={state === 'pending'}
				style:--ui-marker-top="1.125rem"
			>
				<span class="pl-5 text-2xl leading-none font-light text-accent tabular-nums">{i + 1}</span>
				<div class="pl-2">
					<div class="font-bold">
						{s.label}
						{#if state === 'done'}
							<span class="font-normal text-accent">done</span>
						{/if}
					</div>
					{#if latestMessage(s.step)}
						<p class="mt-1 text-xs leading-snug">{latestMessage(s.step)}</p>
					{/if}
				</div>
			</li>
		{/each}
		<li class="mt-6">
			<div class="ui-count text-6xl">{Math.round((last?.progress ?? 0) * 100)}%</div>
			<div class="mt-3 h-1.5 bg-fg/10">
				<div
					class="h-full bg-accent transition-[width] duration-300"
					style:width="{(last?.progress ?? 0) * 100}%"
				></div>
			</div>
		</li>
	</ol>

	<div class="col-span-7 grid min-h-0 grid-cols-4 grid-rows-[auto_1fr] gap-x-4 xl:gap-x-6">
		{#each stats as stat (stat.label)}
			<div class="border-t-2 border-line pt-2">
				<div class="text-6xl leading-[0.85] font-light text-accent tabular-nums">
					{stat.value ?? '–'}
				</div>
				<div class="mt-2 text-sm font-bold">{stat.label}</div>
				{#each stat.notes ?? [] as note (note)}
					<div class="text-xs">{note}</div>
				{/each}
			</div>
		{/each}

		<div class="col-span-2 mt-8 min-h-0 overflow-auto border-t border-line pt-3">
			{#if partial?.profile}
				<div class="ui-label">Understood from spec</div>
				<p class="text-base font-medium">{partial.profile.productType}</p>
				<p class="mt-1 text-xs">{partial.profile.vehicleCategory}</p>
				<ul class="mt-2 space-y-0.5 text-xs">
					{#each partial.profile.functions as f (f)}
						<li>{f}</li>
					{/each}
				</ul>
			{/if}
			{#if included.length}
				<div class="ui-label mt-5">Selected</div>
				<ul class="space-y-1 text-xs">
					{#each included as r (r.regulation)}
						<li><span class="font-bold">{r.regulation}</span> {r.title}</li>
					{/each}
				</ul>
				<div class="ui-label mt-4">Excluded, {excluded.length}</div>
				<p class="text-xs">{excluded.map((r) => r.regulation).join(', ')}</p>
			{/if}
		</div>

		<div class="col-span-2 mt-8 min-h-0 overflow-auto border-t border-line pt-3">
			<div class="ui-label">Requirements found</div>
			<ul class="space-y-1 text-xs">
				{#each (partial?.requirements ?? []).slice(-40).reverse() as r (r.id)}
					<li class="truncate"><span class="mr-3 font-bold">{r.id}</span>{r.text}</li>
				{/each}
			</ul>
		</div>
	</div>
</div>
