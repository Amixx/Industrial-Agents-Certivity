<script lang="ts">
import type { ExplodedAssembly } from './assemblies.ts';

let { assembly }: { assembly: ExplodedAssembly } = $props();

// Scroll distance, in viewport heights, that drives the sequence.
const TRACK = 4;
const LABEL_SPACE = 150;

let scroller: HTMLDivElement | undefined = $state();
let viewH = $state(0);
let areaW = $state(0);
let areaH = $state(0);
let progress = $state(0);
let target = 0;
let frame = 0;

const reduceMotion =
	typeof matchMedia !== 'undefined' && matchMedia('(prefers-reduced-motion: reduce)').matches;

const aspect = $derived(assembly.width / assembly.height);
const stageW = $derived(Math.max(0, Math.min(areaW, (areaH - LABEL_SPACE) * 0.9 * aspect)));
const stageH = $derived(stageW / aspect);
const k = $derived(stageW / assembly.width);
const zoom = $derived(stageH ? Math.min(1.6, Math.max(1, ((areaH - 40) * 0.92) / stageH)) : 1);
// Labels sit on an even column grid under the stage; each part's centre falls in its own column.
const column = $derived(stageW / assembly.parts.length);
/** Too narrow for names and checks, so the labels show just their number; the table below has the rest. */
const compact = $derived(column < 72);

const clamp = (v: number, lo = 0, hi = 1) => Math.min(hi, Math.max(lo, v));
const seg = (p: number, a: number, b: number) => clamp((p - a) / (b - a));
const ease = (t: number) => (t < 0.5 ? 4 * t * t * t : 1 - (-2 * t + 2) ** 3 / 2);
const lerp = (a: number, b: number, t: number) => a + (b - a) * t;

const mid = $derived(Math.floor(assembly.parts.length / 2));
const centre = $derived(assembly.width / 2);

const layers = $derived(
	assembly.parts.map((part, i) => {
		const cx = part.cx ?? part.x + part.w / 2;
		// Once assembled the parts sit a few pixels apart along the stack, rear to the left,
		// unless the assembly says where each one goes.
		const home = part.home ?? centre + (i - mid) * 12;
		const lead = (mid - Math.abs(i - mid)) * 0.02;
		const e = ease(seg(progress, 0.1 + lead, 0.55 + lead));
		const reveal = ease(seg(progress, 0.6 + i * 0.03, 0.72 + i * 0.03));
		return { part, i, cx, dx: (home - cx) * (1 - e) * k, reveal };
	}),
);

const spread = $derived(ease(seg(progress, 0.1, 0.6)));
const scale = $derived(lerp(zoom, 1, spread));
const intro = $derived(1 - seg(progress, 0.02, 0.12));
const outro = $derived(ease(seg(progress, 0.58, 0.7)));

function tickFrame() {
	const diff = target - progress;
	if (Math.abs(diff) < 0.0005) {
		progress = target;
		frame = 0;
		return;
	}
	progress += diff * 0.14;
	frame = requestAnimationFrame(tickFrame);
}

function onScroll() {
	if (!scroller) return;
	const range = scroller.scrollHeight - scroller.clientHeight;
	target = range > 0 ? clamp(scroller.scrollTop / (viewH * (TRACK - 1))) : 0;
	if (reduceMotion) progress = target;
	else if (!frame) frame = requestAnimationFrame(tickFrame);
}

$effect(() => () => cancelAnimationFrame(frame));

const pad = (n: number) => String(n + 1).padStart(2, '0');
</script>

<div
	bind:this={scroller}
	bind:clientHeight={viewH}
	onscroll={onScroll}
	class="min-h-0 flex-1 overflow-x-hidden overflow-y-auto"
>
	<section class="relative" style:height="{viewH * TRACK}px">
		<div class="sticky top-0 flex flex-col overflow-hidden" style:height="{viewH}px">
			<div class="relative h-20 shrink-0 pt-6">
				<div class="absolute inset-x-0 top-6" style:opacity={intro}>
					<span class="ui-label">Exploded view</span>
					<p class="mt-1 text-2xl font-bold tracking-tight">{assembly.name} assembly</p>
					<p class="text-xs">Scroll to take it apart.</p>
				</div>
				<div
					class="absolute inset-x-0 top-6 flex items-end justify-between"
					style:opacity={outro}
					style:transform="translateY({(1 - outro) * 8}px)"
				>
					<div>
						<span class="ui-label">Exploded view</span>
						<p class="mt-1 text-2xl font-bold tracking-tight">
							{assembly.parts.length}
							parts, {assembly.order}
						</p>
					</div>
					<p class="max-w-xs text-right text-xs">Each part with the check it has to pass.</p>
				</div>
			</div>

			<div
				class="flex min-h-0 flex-1 items-center justify-center"
				style:padding-bottom="{LABEL_SPACE}px"
				bind:clientWidth={areaW}
				bind:clientHeight={areaH}
			>
				<div class="relative" style:width="{stageW}px" style:height="{stageH}px">
					<div
						class="absolute inset-x-0 top-1/2 border-t border-dashed border-line"
						style:opacity={spread}
						style:transform="scaleX({spread})"
					></div>

					<div class="absolute inset-0 will-change-transform" style:transform="scale({scale})">
						{#each layers as layer (layer.part.id)}
							<img
								src="{assembly.base}/{layer.part.id}.webp"
								alt={layer.part.name}
								draggable="false"
								class="absolute max-w-none select-none will-change-transform"
								style:left="{layer.part.x * k}px"
								style:top="{layer.part.y * k}px"
								style:width="{layer.part.w * k}px"
								style:height="{layer.part.h * k}px"
								style:transform="translate3d({layer.dx}px, 0, 0)"
								style:z-index={assembly.firstOnTop ? layers.length - layer.i : undefined}
							>
						{/each}
					</div>

					{#each layers as layer (layer.part.id)}
						{@const bottom = (layer.part.y + layer.part.h) * k}
						<div
							class="absolute w-px origin-top bg-faint"
							style:left="{layer.cx * k}px"
							style:top="{bottom + 8}px"
							style:height="{stageH - bottom + 24}px"
							style:transform="scaleY({layer.reveal})"
						></div>
						<div
							class="absolute border-t border-line pt-2 text-xs"
							style:top="{stageH + 32}px"
							style:left="{layer.i * column}px"
							style:width="{column - (compact ? 4 : 16)}px"
							style:opacity={layer.reveal}
							style:transform="translateY({(1 - layer.reveal) * 10}px)"
						>
							<div
								class="{compact
									? 'text-sm'
									: 'text-2xl'} leading-none font-light text-accent tabular-nums"
							>
								{pad(layer.i)}
							</div>
							{#if !compact}
								<div class="mt-2 font-bold">{layer.part.name}</div>
								<div class="mt-0.5 leading-snug">{layer.part.check}</div>
							{/if}
						</div>
					{/each}
				</div>
			</div>
		</div>
	</section>

	<section class="ui-section pb-16">
		<div class="ui-grid pb-3">
			<h2 class="col-span-4 text-sm font-bold">Parts</h2>
			<p class="col-span-8 text-xs">
				Materials are representative values from the spec. The renders are illustrative.
			</p>
		</div>
		<div class="ui-grid border-b-2 border-line pb-1 text-[12px] font-bold">
			<span class="col-span-1">No.</span>
			<span class="col-span-3">Part</span>
			<span class="col-span-3">Material</span>
			<span class="col-span-5">Check</span>
		</div>
		{#each assembly.parts as part, i (part.id)}
			<div class="ui-grid ui-rule-soft items-baseline border-b py-3 text-sm">
				<span class="col-span-1 text-2xl leading-none font-light text-accent tabular-nums"
					>{pad(i)}</span
				>
				<span class="col-span-3 font-bold">{part.name}</span>
				<span class="col-span-3">{part.material}</span>
				<span class="col-span-5">{part.check}</span>
			</div>
		{/each}
	</section>
</div>
