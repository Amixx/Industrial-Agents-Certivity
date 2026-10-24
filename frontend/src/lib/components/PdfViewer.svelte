<script lang="ts">
import type { PDFDocumentProxy, RenderTask } from 'pdfjs-dist';
import { onMount } from 'svelte';
import { findHighlight, type Highlight } from './pdf/highlight.ts';
import { loadDocument, loadPdfJs } from './pdf/loader.ts';

let {
	url,
	page,
	highlight = null,
	class: className = '',
}: {
	url: string;
	page: number;
	highlight?: Highlight | null;
	class?: string;
} = $props();

const PAD = 16;

let scroller: HTMLDivElement;
let pageEl: HTMLDivElement;
let canvas: HTMLCanvasElement;
let textLayerEl: HTMLDivElement;

let doc = $state<PDFDocumentProxy | null>(null);
let docUrl = $state('');
let current = $state(1);
let zoom = $state<'fit' | 1>('fit');
let width = $state(0);
let dpr = $state(1);
let loading = $state(true);
let error = $state('');
let size = $state({ width: 0, height: 0 });
let box = $state<{ left: number; top: number; width: number; height: number } | null>(null);
let notLocated = $state(false);

let renderTask: RenderTask | null = null;
let renderId = 0;

$effect(() => {
	current = page;
});

$effect(() => {
	const target = url;
	loading = true;
	error = '';
	doc = null;
	loadDocument(target).then(
		(d) => {
			if (target !== url) return;
			doc = d;
			docUrl = target;
		},
		(e) => {
			if (target !== url) return;
			error = e instanceof Error ? e.message : String(e);
			loading = false;
		},
	);
});

$effect(() => {
	if (!doc || docUrl !== url || width === 0) return;
	const n = Math.min(Math.max(current, 1), doc.numPages);
	render(doc, n, zoom, width, dpr, n === page ? highlight : null);
});

async function render(
	d: PDFDocumentProxy,
	n: number,
	z: 'fit' | 1,
	w: number,
	ratio: number,
	hl: Highlight | null,
) {
	const id = ++renderId;
	renderTask?.cancel();
	loading = true;
	try {
		const [pdfjs, p] = await Promise.all([loadPdfJs(), d.getPage(n)]);
		const base = p.getViewport({ scale: 1 });
		const scale = z === 'fit' ? Math.max((w - PAD * 2) / base.width, 0.1) : 1;
		const viewport = p.getViewport({ scale });
		const content = await p.getTextContent();
		if (id !== renderId) return;

		canvas.width = Math.floor(viewport.width * ratio);
		canvas.height = Math.floor(viewport.height * ratio);
		size = { width: viewport.width, height: viewport.height };
		pageEl.style.setProperty('--total-scale-factor', String(scale));

		renderTask = p.render({
			canvas,
			viewport,
			transform: ratio === 1 ? undefined : [ratio, 0, 0, ratio, 0, 0],
		});
		await renderTask.promise;
		if (id !== renderId) return;

		textLayerEl.replaceChildren();
		await new pdfjs.TextLayer({
			textContentSource: content,
			container: textLayerEl,
			viewport,
		}).render();
		if (id !== renderId) return;

		const match = hl && (hl.paragraph || hl.text) ? findHighlight(content, hl) : null;
		notLocated = !!hl && (!!hl.paragraph || !!hl.text) && !match;
		if (match) {
			const [x0, y0] = viewport.convertToViewportPoint(match.rect.left - 4, match.rect.top + 2);
			const [x1, y1] = viewport.convertToViewportPoint(match.rect.right + 4, match.rect.bottom - 2);
			box = {
				left: Math.min(x0, x1),
				top: Math.min(y0, y1),
				width: Math.abs(x1 - x0),
				height: Math.abs(y1 - y0),
			};
			scroller.scrollTo({ top: pageEl.offsetTop + box.top - 24 });
		} else {
			box = null;
			scroller.scrollTo({ top: 0 });
		}
		loading = false;
	} catch (e) {
		if (id !== renderId || (e instanceof Error && e.name === 'RenderingCancelledException')) return;
		error = e instanceof Error ? e.message : String(e);
		loading = false;
	}
}

onMount(() => {
	const ro = new ResizeObserver(([entry]) => {
		width = Math.floor(entry.contentRect.width);
	});
	ro.observe(scroller);

	let mq: MediaQueryList;
	const watchDpr = () => {
		dpr = window.devicePixelRatio || 1;
		mq = matchMedia(`(resolution: ${dpr}dppx)`);
		mq.addEventListener('change', onDpr, { once: true });
	};
	const onDpr = () => watchDpr();
	watchDpr();

	return () => {
		ro.disconnect();
		mq.removeEventListener('change', onDpr);
		renderTask?.cancel();
		renderId++;
	};
});

const numPages = $derived(doc?.numPages ?? 0);
</script>

<div
	class="flex min-h-0 flex-col overflow-hidden rounded border border-cv-ink-800/20 bg-white {className}"
>
	<div
		class="flex shrink-0 items-center gap-1 border-b border-cv-ink-800/15 bg-cv-mint-50 px-2 py-1 text-xs text-cv-ink-800"
	>
		<button
			type="button"
			class="rounded px-2 py-0.5 hover:bg-cv-mint-300/50 disabled:opacity-40"
			disabled={current <= 1}
			onclick={() => current--}
			aria-label="Previous page"
		>
			‹
		</button>
		<span class="tabular-nums">page {current} / {numPages || '–'}</span>
		<button
			type="button"
			class="rounded px-2 py-0.5 hover:bg-cv-mint-300/50 disabled:opacity-40"
			disabled={!numPages || current >= numPages}
			onclick={() => current++}
			aria-label="Next page"
		>
			›
		</button>
		<span class="mx-1 h-4 w-px bg-cv-ink-800/20"></span>
		<button
			type="button"
			class="rounded px-2 py-0.5 hover:bg-cv-mint-300/50"
			class:bg-cv-mint-300={zoom === 'fit'}
			onclick={() => (zoom = 'fit')}
		>
			Fit
		</button>
		<button
			type="button"
			class="rounded px-2 py-0.5 hover:bg-cv-mint-300/50"
			class:bg-cv-mint-300={zoom === 1}
			onclick={() => (zoom = 1)}
		>
			100%
		</button>
		{#if notLocated && !loading}
			<span class="ml-2 text-cv-ink-800/60 italic">paragraph not located</span>
		{/if}
		<a
			class="ml-auto rounded px-2 py-0.5 text-cv-teal-700 hover:bg-cv-mint-300/50"
			href="{url}#page={current}"
			target="_blank"
			rel="noopener"
			>Open PDF ↗</a
		>
	</div>

	<div bind:this={scroller} class="relative min-h-0 flex-1 overflow-auto bg-cv-ink-800/5">
		<div
			bind:this={pageEl}
			class="pdf-page relative mx-auto my-4 bg-white shadow"
			class:invisible={!!error}
			style:width="{size.width}px"
			style:height="{size.height}px"
		>
			<canvas bind:this={canvas} class="absolute inset-0 h-full w-full"></canvas>
			{#if box}
				<div
					class="pointer-events-none absolute border-l-4 border-cv-teal-700 bg-cv-mint-300/40 mix-blend-multiply"
					style:left="{box.left}px"
					style:top="{box.top}px"
					style:width="{box.width}px"
					style:height="{box.height}px"
				></div>
			{/if}
			<div bind:this={textLayerEl} class="textLayer"></div>
		</div>

		{#if loading && !error}
			<div
				class="absolute inset-0 flex items-center justify-center bg-white/60 text-sm text-cv-ink-800"
			>
				Loading…
			</div>
		{/if}
		{#if error}
			<div
				class="absolute inset-0 flex items-center justify-center p-4 text-center text-sm text-cv-ink-800"
			>
				Could not load PDF: {error}
			</div>
		{/if}
	</div>
</div>

<style>
.pdf-page {
	--scale-round-x: 1px;
	--scale-round-y: 1px;
}
.pdf-page :global(.textLayer) {
	position: absolute;
	inset: 0;
	overflow: clip;
	line-height: 1;
	text-align: initial;
	text-size-adjust: none;
	forced-color-adjust: none;
	transform-origin: 0 0;
	z-index: 2;
	--min-font-size: 1;
	--text-scale-factor: calc(var(--total-scale-factor) * var(--min-font-size));
	--min-font-size-inv: calc(1 / var(--min-font-size));
}
.pdf-page :global(.textLayer :is(span, br)) {
	color: transparent;
	position: absolute;
	white-space: pre;
	cursor: text;
	transform-origin: 0% 0%;
}
.pdf-page :global(.textLayer > :not(.markedContent)),
.pdf-page :global(.textLayer .markedContent span:not(.markedContent)) {
	z-index: 1;
	--font-height: 0;
	font-size: calc(var(--text-scale-factor) * var(--font-height));
	--scale-x: 1;
	--rotate: 0deg;
	transform: rotate(var(--rotate)) scaleX(var(--scale-x)) scale(var(--min-font-size-inv));
}
.pdf-page :global(.textLayer .markedContent) {
	display: contents;
}
.pdf-page :global(.textLayer ::selection) {
	background: rgb(11 122 112 / 0.3);
}
.pdf-page :global(.textLayer .endOfContent) {
	display: block;
	position: absolute;
	inset: 100% 0 0;
	z-index: 0;
	cursor: default;
	user-select: none;
}
</style>
