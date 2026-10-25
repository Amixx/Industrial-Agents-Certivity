<script lang="ts">
import type { PartCoverage } from '#lib/graph/model.ts';

let {
	number,
	name,
	coverage,
	x,
	y,
	width,
	height,
}: {
	number: string;
	name: string;
	coverage: PartCoverage;
	/** Pointer position inside the model area. */
	x: number;
	y: number;
	/** Size of the model area, to keep the card inside it. */
	width: number;
	height: number;
} = $props();
</script>

<div
	class="pointer-events-none absolute z-10 w-60 border border-line bg-panel px-3 pt-2 pb-2.5"
	style:left="{Math.min(x + 16, width - 256)}px"
	style:top="{y + 16}px"
	style:translate={y > height / 2 ? '0 calc(-100% - 32px)' : undefined}
>
	<div class="flex items-baseline gap-2">
		<span class="text-sm leading-none font-light text-accent tabular-nums">{number}</span>
		<span class="text-sm font-bold">{name}</span>
	</div>
	<dl class="mt-2 grid grid-cols-3 gap-x-3 border-t border-line pt-1">
		<div class="flex flex-col-reverse">
			<dt class="mt-1 text-[11.5px]">Regulations</dt>
			<dd class="text-2xl leading-none font-light text-accent tabular-nums">
				{coverage.regulations.length}
			</dd>
		</div>
		<div class="flex flex-col-reverse">
			<dt class="mt-1 text-[11.5px]">Requirements</dt>
			<dd class="text-2xl leading-none font-light text-accent tabular-nums">
				{coverage.requirements}
			</dd>
		</div>
		<div class="flex flex-col-reverse">
			<dt class="mt-1 text-[11.5px]">Paragraphs</dt>
			<dd class="text-2xl leading-none font-light text-accent tabular-nums">
				{coverage.paragraphs}
			</dd>
		</div>
	</dl>
	{#if coverage.regulations.length}
		<ul class="mt-2 space-y-0.5 border-t border-line pt-1.5 text-[12px]">
			{#each coverage.regulations as reg (reg.regulation)}
				<li class="flex justify-between gap-2">
					<span class="font-bold">{reg.regulation}</span>
					<span class="tabular-nums">
						{reg.requirements.length
							? `${reg.requirements.length} requirements`
							: 'named in the selection reason'}
					</span>
				</li>
			{/each}
		</ul>
	{:else}
		<p class="mt-2 border-t border-line pt-1.5 text-[12px]">No regulation mentions this part.</p>
	{/if}
	<p class="mt-2 text-[12px] text-muted">Click to open it in the graph.</p>
</div>
