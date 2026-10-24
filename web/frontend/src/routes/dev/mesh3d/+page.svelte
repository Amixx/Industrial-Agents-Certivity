<script lang="ts">
import { onMount } from 'svelte';
import type { Manifest } from '#lib/mesh3d/viewer.js';

let host: HTMLDivElement;
let manifest = $state.raw<Manifest | null>(null);
let selectedId = $state<string | null>(null);
let hoveredId = $state<string | null>(null);
let explosion = $state(1);
let status = $state('Loading meshes…');
let error = $state('');
let viewer: ReturnType<typeof import('#lib/mesh3d/viewer.js').createViewer> | undefined;
const selected = $derived(manifest?.parts.find((part) => part.id === selectedId));
const hovered = $derived(manifest?.parts.find((part) => part.id === hoveredId));
const requirements = $derived(
	manifest?.requirements.filter((r) => selected?.requirementIds.includes(r.id)) ?? [],
);

function select(id: string) {
	selectedId = id;
	viewer?.select(id);
}
function explode(event: Event) {
	explosion = Number((event.currentTarget as HTMLInputElement).value);
	viewer?.explode(explosion);
}
onMount(() => {
	let cancelled = false;
	async function start() {
		try {
			const response = await fetch('/mesh3d/dev-rear-lamp/manifest.json');
			if (!response.ok) throw new Error(`Manifest: HTTP ${response.status}`);
			const data: Manifest = await response.json();
			const { createViewer } = await import('#lib/mesh3d/viewer.js');
			if (cancelled) return;
			manifest = data;
			viewer = createViewer(host, data.parts, select, (id) => {
				hoveredId = id;
			});
			await viewer.ready;
			if (!cancelled)
				status = `${data.parts.filter((p) => p.file).length} / ${data.parts.length} meshes loaded`;
		} catch (cause) {
			if (!cancelled) error = cause instanceof Error ? cause.message : String(cause);
		}
	}
	void start();
	return () => {
		cancelled = true;
		viewer?.dispose();
	};
});
</script>

<svelte:head>
	<title>3D parts spike / sudo</title>
	<link
		rel="stylesheet"
		href="https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@300;400;500;600;700&display=swap"
	>
</svelte:head>

<main>
	<header>
		<div class="brand">sudo <span>in collaboration with Certivity</span></div>
		<span class="label">Development / 3D parts spike</span>
	</header>
	<section class="heading">
		<div>
			<p class="label">01 / Rear lamp</p>
			<h1>From drawing to parts.</h1>
		</div>
		<p class="intro">
			Real generated meshes, not image layers.<br>Drag to orbit. Select a part to inspect its rules.
		</p>
	</section>
	<div class="workspace">
		<section class="stage" aria-label="3D parts viewer">
			<div class="stage-bar">
				<span class="label">{explosion === 0 ? 'Assembled' : 'Exploded'} / inferred layout</span
				><button onclick={() => viewer?.reset()}>Reset camera</button>
			</div>
			<div class="canvas" bind:this={host}></div>
			<div class="stage-caption">
				<span>{hovered?.name ?? 'Drag to orbit / scroll to zoom'}</span
				><span role="status">{error || status}</span>
			</div>
			<div class="explode">
				<label for="explode">Explode</label><span>Assembled</span>
				<input
					id="explode"
					type="range"
					min="0"
					max="1"
					step="0.01"
					value={explosion}
					oninput={explode}
				><span>Exploded</span><output for="explode">{Math.round(explosion * 100)}%</output>
			</div>
		</section>
		<aside aria-live="polite">
			<p class="label">Part requirements</p>
			{#if selected}
				<h2>{selected.name}</h2>
				<p class="count">{requirements.length} keyword-linked requirements</p>
				<div class="requirements">
					{#each requirements as requirement (requirement.id)}
						<article>
							<div class="req-meta">
								<strong>{requirement.id}</strong
								><span>{requirement.source.regulation} / p. {requirement.source.page}</span>
							</div>
							<p>{requirement.text}</p>
						</article>
					{:else}
						<p>No linked requirements.</p>
					{/each}
				</div>
			{:else}
				<h2>Select a part.</h2>
				<p class="empty">
					Click a mesh or use the part list below. Its linked requirements and source pages will
					appear here.
				</p>
				<img
					class="source"
					src="/parts3d/dev-rear-lamp/exploded_view.png"
					alt="Original rear lamp body and detached lens line drawing"
				>
				<p class="label">Source drawing</p>
			{/if}
		</aside>
	</div>
	<nav aria-label="Select a part">
		{#each manifest?.parts ?? [] as part (part.id)}
			<button class:active={selectedId === part.id} onclick={() => select(part.id)}>
				<span class="number">{String(part.order + 1).padStart(2, '0')}</span>
				{part.name}
				{#if !part.file}
					<small> / no mesh</small>
				{/if}
			</button>
		{/each}
	</nav>
	<footer>
		<strong>Experimental geometry.</strong>
		Shapes, scale and assembly positions are inferred, not recovered CAD. The supplied regions
		overlap. Requirement links are keyword matches, not reviewed compliance decisions.
	</footer>
</main>

<style>
:global(body) {
	margin: 0;
	background: white;
}
main {
	font-family: "Hanken Grotesk", sans-serif;
	color: #02312f;
	padding: 0 40px 24px;
	max-width: 1600px;
	margin: auto;
}
header {
	height: 92px;
	display: flex;
	align-items: center;
	justify-content: space-between;
	border-bottom: 1px solid #cbd5d1;
}
.brand {
	font-size: 44px;
	font-weight: 600;
	letter-spacing: -3px;
	display: flex;
	align-items: baseline;
	gap: 22px;
}
.brand span {
	font-size: 12px;
	font-weight: 400;
	letter-spacing: 0;
}
.label {
	font-size: 11px;
	text-transform: uppercase;
	letter-spacing: 1.5px;
}
.heading {
	display: flex;
	justify-content: space-between;
	align-items: end;
	padding: 28px 0;
}
h1 {
	font-size: 48px;
	font-weight: 400;
	line-height: 1.1;
	letter-spacing: -1.8px;
	margin: 10px 0 0;
}
.intro {
	font-size: 15px;
	line-height: 1.5;
	margin: 0;
	color: #42635b;
}
.workspace {
	display: grid;
	grid-template-columns: minmax(0, 1fr) 350px;
	border-top: 1px solid #a8bdb5;
	border-bottom: 1px solid #a8bdb5;
}
.stage {
	min-width: 0;
}
.stage-bar,
.stage-caption {
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding: 14px 20px 14px 0;
}
.stage-caption {
	font-size: 12px;
	color: #42635b;
}
button {
	font: inherit;
	cursor: pointer;
	border: 0;
	background: none;
	color: inherit;
}
button:focus-visible,
input:focus-visible {
	outline: 2px solid #0b7a70;
	outline-offset: 3px;
}
.stage-bar button {
	font-size: 12px;
	text-decoration: underline;
	text-underline-offset: 4px;
}
.canvas {
	width: 100%;
	height: 360px;
}
.canvas :global(canvas) {
	display: block;
	touch-action: none;
}
.explode {
	display: flex;
	align-items: center;
	gap: 16px;
	border-top: 1px solid #cbd5d1;
	padding: 20px 24px 20px 0;
	font-size: 12px;
}
.explode label {
	font-size: 16px;
	margin-right: 12px;
}
input {
	flex: 1;
	min-width: 40px;
	accent-color: #0b7a70;
	cursor: pointer;
}
output {
	width: 36px;
	text-align: right;
	font-variant-numeric: tabular-nums;
}
aside {
	border-left: 1px solid #a8bdb5;
	padding: 18px 0 0 26px;
}
h2 {
	font-size: 28px;
	font-weight: 400;
	line-height: 1.15;
	margin: 18px 0 8px;
}
.count,
.empty {
	font-size: 14px;
	line-height: 1.5;
	color: #42635b;
}
.requirements {
	height: 370px;
	overflow-y: auto;
	padding-right: 12px;
}
article {
	border-top: 1px solid #cbd5d1;
	padding: 14px 0;
}
.req-meta {
	display: flex;
	justify-content: space-between;
	font-size: 11px;
	color: #0b7a70;
}
article p {
	font-size: 13px;
	line-height: 1.55;
	margin: 10px 0 0;
}
.source {
	width: 230px;
	max-height: 240px;
	object-fit: contain;
	margin: 18px 0;
}
nav {
	display: flex;
	border-bottom: 1px solid #a8bdb5;
}
nav button {
	text-align: left;
	flex: 1;
	font-size: 13px;
	padding: 18px 10px;
	border-right: 1px solid #cbd5d1;
}
nav button:first-child {
	padding-left: 0;
}
nav button:last-child {
	border-right: 0;
}
nav button.active {
	background: #e9faf5;
	box-shadow: inset 0 -3px #0b7a70;
}
.number {
	color: #0b7a70;
	margin-right: 10px;
	font-size: 20px;
	font-weight: 300;
}
footer {
	font-size: 12px;
	color: #42635b;
	line-height: 1.6;
	padding-top: 18px;
	max-width: 1000px;
}
@media (max-width: 900px) {
	main {
		padding: 0 20px 20px;
	}
	.workspace {
		grid-template-columns: 1fr;
	}
	aside {
		border-left: 0;
		border-top: 1px solid #a8bdb5;
		padding: 20px 0;
	}
	.heading {
		display: block;
	}
	.intro {
		margin-top: 16px;
	}
	header > .label {
		display: none;
	}
	nav {
		flex-wrap: wrap;
	}
	nav button {
		flex-basis: 30%;
	}
	h1 {
		font-size: 38px;
	}
}
</style>
