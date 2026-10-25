<script lang="ts">
import { onMount } from 'svelte';
import { api } from '#lib/api/client.ts';
import type { Assessment } from '#lib/api/types.ts';
import type { LampScene } from '#lib/exploded/lamp3d.ts';
import PartHoverCard from '#lib/exploded/PartHoverCard.svelte';
import { rearLamp } from '#lib/exploded/rearLamp.ts';
import { buildGraph, partCoverage, partFacets } from '#lib/graph/model.ts';
import { colorScheme } from '#lib/ui/colorScheme.svelte.ts';
import Wordmark from '#lib/ui/Wordmark.svelte';
import { goto, onNavigate } from '$app/navigation';

/** The saved rear lamp assessment the lamp's numbers and links come from. */
const SHOWCASE_ID = 'f14b0208';
/** How long the model must sit untouched before the tour picks up again. */
const TOUR_IDLE_MS = 5000;
const TOUR_STEP_MS = 3200;
/** From the scene appearing to the tour's first part: the explode, then a few seconds to look. */
const TOUR_START_MS = 4700;
/** How long the camera takes to fly in to a clicked part before the page changes. */
const FLIGHT_MS = 700;

let assessment = $state<Assessment | null>(null);
let host: HTMLDivElement | undefined = $state();
let scene: LampScene | null = $state(null);
let explode = $state(0);
let lit = $state(false);
let hoveredId: string | null = $state(null);
let cursor = $state({ x: 0, y: 0 });
let viewportWidth = $state(0);
/** The part the idle tour is showing, and where its card sits. */
let tourId: string | null = $state(null);
let tourPoint = $state({ x: 0, y: 0 });
let lastTouch = 0;
/** The part that was clicked, while the page flies in to it. */
let openingId: string | null = $state(null);
let openingAt = $state({ x: 0, y: 0 });

const pad = (n: number) => String(n + 1).padStart(2, '0');
const shownId = $derived(openingId ?? hoveredId ?? tourId);
const shownIndex = $derived(rearLamp.parts.findIndex((p) => p.id === shownId));
const shownAt = $derived(openingId ? openingAt : hoveredId ? cursor : tourPoint);

const coverage = $derived.by(() => {
	if (!assessment) return {};
	const graph = buildGraph(assessment);
	const { requirements } = assessment;
	return Object.fromEntries(
		rearLamp.parts.map((p) => [p.id, partCoverage(partFacets(graph, p), requirements)]),
	);
});
const shownCoverage = $derived(shownId ? coverage[shownId] : undefined);
/** The first requirement cited for the part on show, quoted under the headline. */
const citation = $derived.by(() => {
	const reg = shownCoverage?.regulations.find((r) => r.requirements.length);
	return reg ? { reg: reg.regulation, req: reg.requirements[0] } : null;
});
const tourParts = $derived(
	rearLamp.parts.filter((p) => coverage[p.id]?.regulations.length).map((p) => p.id),
);

const stats = $derived(
	assessment
		? [
				{ value: assessment.regulations.length, label: 'Regulations checked' },
				{ value: assessment.regulations.filter((r) => r.included).length, label: 'Apply' },
				{ value: assessment.requirements.length, label: 'Requirements' },
				{
					value: new Set(
						assessment.requirements.map((r) => `${r.source.regulation} ${r.source.paragraph}`),
					).size,
					label: 'Source paragraphs',
				},
			]
		: [],
);

function open(id: string) {
	if (!assessment || !scene || openingId) return;
	openingAt =
		hoveredId === id ? cursor : tourId === id ? tourPoint : (scene.screenPoint(id) ?? cursor);
	openingId = id;
	tourId = null;
	scene.focus(id, FLIGHT_MS);
	setTimeout(() => goto(`/a/${assessment?.id}/graph?part=${id}`), FLIGHT_MS - 150);
}

// The landing zooms away and the clicked part's card becomes the graph's part panel.
onNavigate((navigation) => {
	if (!openingId || !document.startViewTransition) return;
	const root = document.documentElement;
	root.dataset.transition = 'part';
	return new Promise((resolve) => {
		const transition = document.startViewTransition(async () => {
			resolve();
			await navigation.complete;
		});
		transition.finished.finally(() => delete root.dataset.transition);
	});
});

function touch() {
	lastTouch = performance.now();
	if (tourId && !openingId) tourId = null;
}

function track(e: PointerEvent) {
	if (!host || !hoveredId) return;
	const rect = host.getBoundingClientRect();
	cursor = { x: e.clientX - rect.left, y: e.clientY - rect.top };
}

onMount(() => {
	api.getAssessment(SHOWCASE_ID).then((a) => (assessment = a));

	let disposed = false;
	let created: LampScene | null = null;
	const timers: ReturnType<typeof setTimeout>[] = [];
	import('#lib/exploded/lamp3d.ts').then(({ createLampScene }) => {
		if (disposed || !host) return;
		created = createLampScene(
			host,
			rearLamp.parts.map((p, i) => ({ id: p.id, number: pad(i), name: p.name })),
			(id) => id && open(id),
			(id) => {
				if (!openingId) hoveredId = id;
			},
		);
		scene = created;
		timers.push(setTimeout(() => (explode = 1), 700));
		// One blink, then it stays on.
		for (const [at, on] of [
			[2200, true],
			[2380, false],
			[2600, true],
		] as const)
			timers.push(setTimeout(() => (lit = on), at));
		timers.push(
			setTimeout(() => {
				showNext();
				tour = setInterval(showNext, TOUR_STEP_MS);
			}, TOUR_START_MS),
		);
	});
	// Until someone reaches for the model, step through the parts so it shows what hovering does.
	let step = 0;
	let tour: ReturnType<typeof setInterval> | undefined;
	const showNext = () => {
		if (!scene || !tourParts.length || hoveredId || openingId) return;
		if (performance.now() - lastTouch < TOUR_IDLE_MS) return;
		const id = tourParts[step++ % tourParts.length];
		tourPoint = scene.screenPoint(id) ?? tourPoint;
		tourId = id;
	};
	return () => {
		disposed = true;
		clearInterval(tour);
		for (const t of timers) clearTimeout(t);
		created?.dispose();
	};
});

$effect(() => scene?.setExplode(explode));
$effect(() => scene?.setLit(lit));
$effect(() => scene?.setSelected(tourId));
// The intro text holds the left of the screen on wide viewports; below that it sits over the model.
$effect(() => scene?.setInset(viewportWidth >= 1024 ? 0.4 : 0));
</script>

<svelte:head><title>sudo | UN Regulations for every part</title></svelte:head>

<svelte:window onpointermove={track} bind:innerWidth={viewportWidth} />

<div class="ui-app relative h-screen overflow-hidden">
	<div
		bind:this={host}
		class="lamp3d absolute inset-0 cursor-grab active:cursor-grabbing"
		onpointermovecapture={touch}
		onpointerdowncapture={touch}
		onwheelcapture={touch}
	>
		{#if shownId && shownCoverage}
			<PartHoverCard
				number={pad(shownIndex)}
				name={rearLamp.parts[shownIndex].name}
				coverage={shownCoverage}
				x={shownAt.x}
				y={shownAt.y}
				width={host?.clientWidth ?? 0}
				height={host?.clientHeight ?? 0}
				transitionName={openingId ? 'part-card' : undefined}
			/>
		{/if}
	</div>

	<header
		class="ui-gutter pointer-events-none absolute inset-x-0 top-0 z-20 flex items-center justify-between py-4"
	>
		<div class="pointer-events-auto"><Wordmark /></div>
		<nav class="pointer-events-auto flex items-center gap-1">
			<a
				href="/about"
				class="flex h-8 items-center rounded-button px-3 text-xs font-medium text-muted hover:bg-fg/5 hover:text-fg"
			>
				About
			</a>
			<a
				href="/history"
				class="flex h-8 items-center rounded-button px-3 text-xs font-medium text-muted hover:bg-fg/5 hover:text-fg"
			>
				History
			</a>
			<button
				type="button"
				class="flex h-8 cursor-pointer items-center rounded-button px-3 font-mono text-[10.5px] tracking-[0.08em] text-muted uppercase hover:text-fg"
				onclick={() => colorScheme.toggle()}
			>
				{colorScheme.current === 'dark' ? 'Light' : 'Dark'}
			</button>
			<a href="/new" class="ui-btn ui-btn-primary ml-2">Start an assessment</a>
		</nav>
	</header>

	<section
		class="ui-gutter intro pointer-events-none absolute bottom-0 left-0 z-20 w-full pb-10 md:w-auto md:max-w-[40rem]"
	>
		<span class="ui-label">Type approval, rear lamp example</span>
		<h1 class="mt-4 text-[2.5rem] leading-[0.95] font-bold tracking-[-0.045em] md:text-[3.75rem]">
			Point at a part.<br>
			Read the paragraph<br>
			it has to meet.
		</h1>
		<div class="mt-6 h-[5.5rem] border-l-2 border-mark pl-4" aria-live="polite">
			{#if citation && shownId}
				{#key shownId}
					<div class="cite">
						<div class="flex items-baseline gap-3 font-mono text-[12px] tabular-nums">
							<span class="text-accent">{pad(shownIndex)}</span>
							<span class="font-medium text-fg">{rearLamp.parts[shownIndex].name}</span>
							<span class="text-muted">
								{citation.reg}
								§ {citation.req.source.paragraph}, p. {citation.req.source.page}
							</span>
						</div>
						<p class="mt-1.5 line-clamp-3 max-w-[52ch] text-[13px] leading-snug text-muted">
							{citation.req.text}
						</p>
					</div>
				{/key}
			{:else}
				<p class="max-w-[46ch] text-sm leading-relaxed text-muted">
					sudo reads a product spec, finds the UN Regulations that apply, explains the ones it rules
					out and cites every requirement to its page and paragraph.
				</p>
			{/if}
		</div>
		{#if stats.length}
			<dl class="mt-7 flex gap-8 border-t border-line pt-4">
				{#each stats as s (s.label)}
					<div class="flex flex-col-reverse">
						<dt class="ui-label mt-2">{s.label}</dt>
						<dd class="ui-count text-5xl">{s.value}</dd>
					</div>
				{/each}
			</dl>
		{/if}
		<div class="pointer-events-auto mt-7 flex flex-wrap gap-2">
			<a href="/new" class="ui-btn ui-btn-primary h-10 px-4 text-sm">Start an assessment</a>
			{#if assessment}
				<a href="/a/{assessment.id}" class="ui-btn h-10 bg-canvas px-4 text-sm">
					Open the example report
				</a>
			{/if}
		</div>
	</section>

	<div
		class="ui-gutter pointer-events-none absolute right-0 bottom-0 z-20 hidden flex-col items-end gap-3 pb-10 md:flex"
	>
		<span class="ui-label">Click a part to open its graph</span>
		<div class="pointer-events-auto flex items-center gap-4">
			<label class="flex items-center gap-3 text-xs font-bold">
				<span>Assembled</span>
				<input
					type="range"
					min="0"
					max="1"
					step="0.01"
					bind:value={explode}
					class="w-40 accent-accent"
					aria-label="Explode distance"
				>
				<span>Exploded</span>
			</label>
			<button
				type="button"
				class="ui-toggle {lit ? 'ui-toggle-on' : ''}"
				onclick={() => (lit = !lit)}
			>
				{lit ? 'Lamp on' : 'Lamp off'}
			</button>
		</div>
	</div>
</div>

<style>
.intro > :global(*) {
	animation: rise 900ms cubic-bezier(0.2, 0.7, 0.2, 1) both;
}
.intro > :global(:nth-child(2)) {
	animation-delay: 120ms;
}
.intro > :global(:nth-child(3)) {
	animation-delay: 240ms;
}
.cite {
	animation: rise 420ms cubic-bezier(0.2, 0.7, 0.2, 1) both;
}
.intro > :global(:nth-child(4)) {
	animation-delay: 1400ms;
}
.intro > :global(:nth-child(5)) {
	animation-delay: 1600ms;
}
@keyframes rise {
	from {
		opacity: 0;
		translate: 0 1.25rem;
	}
}
@media (prefers-reduced-motion: reduce) {
	.intro > :global(*),
	.cite {
		animation: none;
	}
}
</style>
