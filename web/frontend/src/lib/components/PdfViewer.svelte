<script lang="ts">
import type { PDFDocumentProxy, RenderTask } from 'pdfjs-dist';
import { onMount, type Snippet } from 'svelte';
import { findHighlight, type Highlight } from './pdf/highlight.ts';
import { loadDocument, loadPdfJs } from './pdf/loader.ts';

let {
	url,
	page,
	highlight = null,
	label = '',
	class: className = '',
	children,
}: {
	url: string;
	page: number;
	highlight?: Highlight | null;
	/** Shown as a tag on the highlighted paragraph. */
	label?: string;
	class?: string;
	/** Rendered inside the scrolling area, so absolutely placed content scrolls with the page. */
	children?: Snippet;
} = $props();

const PAD = 16;
const toggle = 'h-7 cursor-pointer rounded-control px-2 font-bold hover:bg-fg/5';
const toggleOn = 'bg-select text-fg hover:bg-select';

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
			const room = scroller.clientHeight - box.height;
			scroller.scrollTo({
				top: pageEl.offsetTop + box.top - Math.max(Math.min(room / 3, 160), 32),
				behavior: 'smooth',
			});
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

<div class="flex min-h-0 flex-col overflow-hidden bg-canvas {className}">
	<div class="flex shrink-0 items-center gap-1 border-b border-line py-1.5 text-xs font-medium">
		<button
			type="button"
			class="{toggle} disabled:opacity-30"
			disabled={current <= 1}
			onclick={() => current--}
			aria-label="Previous page"
		>
			‹
		</button>
		<span class="tabular-nums">Page {current} / {numPages || '–'}</span>
		<button
			type="button"
			class="{toggle} disabled:opacity-30"
			disabled={!numPages || current >= numPages}
			onclick={() => current++}
			aria-label="Next page"
		>
			›
		</button>
		<span class="mx-2 h-4 w-px bg-fg/20"></span>
		<button
			type="button"
			class="{toggle} {zoom === 'fit' ? toggleOn : ''}"
			onclick={() => (zoom = 'fit')}
		>
			Fit
		</button>
		<button type="button" class="{toggle} {zoom === 1 ? toggleOn : ''}" onclick={() => (zoom = 1)}>
			100%
		</button>
		{#if notLocated && !loading}
			<span class="ml-2 text-muted">Paragraph not located</span>
		{/if}
		<a
			class="ml-auto underline decoration-1 underline-offset-2 hover:text-accent"
			href="{url}#page={current}"
			target="_blank"
			rel="noopener"
			>Open PDF ↗</a
		>
	</div>

	<div bind:this={scroller} class="relative min-h-0 flex-1 overflow-auto bg-panel">
		<div
			bind:this={pageEl}
			class="pdf-page relative mx-auto my-4 bg-white outline outline-1 outline-line"
			class:invisible={!!error}
			style:width="{size.width}px"
			style:height="{size.height}px"
		>
			<canvas bind:this={canvas} class="absolute inset-0 h-full w-full"></canvas>
			{#if box}
				<div class="spot pointer-events-none absolute inset-0 overflow-hidden">
					<div
						class="mark absolute"
						style:left="{box.left}px"
						style:top="{box.top}px"
						style:width="{box.width}px"
						style:height="{box.height}px"
					>
						{#if label}
							<span class="tag">{label}</span>
						{/if}
					</div>
				</div>
			{/if}
			<div bind:this={textLayerEl} class="textLayer"></div>
		</div>

		{@render children?.()}

		{#if loading && !error}
			<div class="absolute inset-0 flex items-center justify-center bg-canvas/60 text-sm">
				Loading…
			</div>
		{/if}
		{#if error}
			<div class="absolute inset-0 flex items-center justify-center p-4 text-center text-sm">
				Could not load PDF: {error}
			</div>
		{/if}
	</div>
</div>

<style>
/* The rest of the page is dimmed by a wide outline around the highlighted paragraph. */
.mark {
	box-sizing: border-box;
	outline: 200vmax solid rgb(0 0 0 / 0.05);
	border: 2px solid black;
	border-radius: 3px;
	background: color-mix(in srgb, var(--color-cv-mint-300) 30%, transparent);
}
.tag {
	position: absolute;
	bottom: 100%;
	left: 0;
	margin-bottom: 4px;
	padding: 1px 6px;
	background: black;
	color: white;
	font-size: 12px;
	font-weight: 700;
	white-space: nowrap;
	border-radius: 2px;
}
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
