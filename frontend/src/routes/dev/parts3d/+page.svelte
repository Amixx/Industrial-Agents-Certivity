<script lang="ts">
	import { onMount } from 'svelte';
	type Requirement = { id: string; text: string; source: { regulation: string; version: string; page: number; paragraph: string } };
	type Part = { id: string; name: string; shortName: string; accent: string; depth: number; polygon: [number, number][]; keywords: string[] };
	let parts = $state<Part[]>([]);
	let requirements = $state<Requirement[]>([]);
	let selectedId = $state('outer-lens');
	let tilt = $state({ x: 0, y: 0 });
	let loaded = $state(false);
	const selected = $derived(parts.find((part) => part.id === selectedId) ?? parts[3]);
	const relevant = $derived(requirements.filter((requirement) => selected?.keywords.some((keyword) => `${requirement.text} ${requirement.source.regulation}`.toLowerCase().includes(keyword))).slice(0, 5));

	function selectPart(id: string) { selectedId = id; }
	function moveStage(event: PointerEvent) {
		const rect = (event.currentTarget as HTMLElement).getBoundingClientRect();
		tilt = { x: ((event.clientY - rect.top) / rect.height - 0.5) * -7, y: ((event.clientX - rect.left) / rect.width - 0.5) * 9 };
	}
	function resetStage() { tilt = { x: 0, y: 0 }; }
	onMount(() => {
		Promise.all([
			fetch('/parts3d/dev-rear-lamp/regions.json').then((response) => response.json()),
			fetch('/parts3d/dev-rear-lamp/expected.json').then((response) => response.json()),
		]).then(([regionData, expected]) => { parts = regionData.parts; requirements = expected.requirements; loaded = true; });
	});
</script>

<svelte:head>
	<title>Parts view · sudo</title>
	<meta name="description" content="Clickable 2.5D exploded parts view for sudo." />
	<link rel="preconnect" href="https://fonts.googleapis.com" />
	<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous" />
	<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Space+Grotesk:wght@400;500;600;700&display=swap" />
</svelte:head>

<main class="min-h-screen bg-cv-ink-950 text-cv-mint-50">
	<header class="mx-auto flex max-w-[1440px] items-center justify-between px-6 py-5 lg:px-10">
		<div class="flex items-center gap-4"><div class="brand-mark">s</div><div><div class="brand-name">sudo</div><div class="eyebrow">CERTIVITY / PARTS INTELLIGENCE</div></div></div>
		<div class="hidden items-center gap-4 text-right sm:flex"><div class="eyebrow">CASE</div><div class="mono text-sm text-cv-mint-300">DEV-REAR-LAMP</div></div>
	</header>
	<section class="mx-auto max-w-[1440px] px-6 pb-10 lg:px-10">
		<div class="mb-7 max-w-3xl"><p class="eyebrow mb-3 text-cv-teal-400">EXPLODED VIEW / INTERACTIVE PROTOTYPE</p><h1>Trace every part back to its rules.</h1><p class="intro">A lightweight 2.5D reading of the supplied drawing. Hover to orbit the paper-cut layers, then select a component to see the requirements it brings with it.</p></div>
		<div class="grid gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
			<section class="stage-shell" aria-label="Interactive exploded parts view">
				<div class="stage-topline"><span>VIEW / FRONT EXPLODED</span><span class="mono">NTS · 05 PARTS</span></div>
				<div class="stage" role="application" aria-label="Orbitable parts drawing" onpointermove={moveStage} onpointerleave={resetStage}>
					<div class="stage-grid"></div>
					<div class="paper-stack" style={`--tilt-x:${tilt.x}deg; --tilt-y:${tilt.y}deg`}>
						<div class="paper-shadow"></div><img class="drawing" src="/parts3d/dev-rear-lamp/exploded_view.png" alt="Rear lamp exploded-view line drawing" />
						{#each parts as part (part.id)}
							<button class:selected={selectedId === part.id} class="region" style={`--region:${part.polygon.map(([x, y]) => `${x * 100}% ${y * 100}%`).join(',')}; --accent:${part.accent}; --depth:${part.depth * 5}px`} title={`Select ${part.name}`} aria-label={`Select ${part.name}`} onclick={() => selectPart(part.id)}><span class="region-tag">{String(part.depth + 1).padStart(2, '0')}</span></button>
						{/each}
					</div>
					<div class="stage-note"><span class="live-dot"></span> pointer movement adds depth</div>
				</div>
				<div class="stage-footer"><span>Source drawing · supplied patent-style assembly view</span><span class="mono">REGION MAP / {loaded ? 'LOADED' : 'LOADING'}</span></div>
			</section>
			<aside class="inspector" aria-live="polite">
				<div class="inspector-kicker"><span class="live-dot"></span> SELECTED COMPONENT</div>
				{#if selected}
					<div class="selected-heading"><span class="part-number" style={`--accent:${selected.accent}`}>{String(selected.depth + 1).padStart(2, '0')}</span><div><h2>{selected.name}</h2><p>Rear lamp assembly · mapped from source image</p></div></div>
					<div class="rule-count"><strong>{relevant.length}</strong><span>matched requirements<br />from expected result</span></div>
					<div class="requirement-list">{#each relevant as requirement (requirement.id)}<article class="requirement"><div class="req-meta"><span>{requirement.id}</span><span>{requirement.source.regulation} · p.{requirement.source.page}</span></div><p>{requirement.text}</p></article>{:else}<p class="empty">No keyword match in the demo result.</p>{/each}</div>
				{/if}
			</aside>
		</div>
		<div class="part-strip" aria-label="Parts selector"><div class="eyebrow">PARTS / CLICK TO INSPECT</div><div class="part-buttons">{#each parts as part (part.id)}<button class:active={selectedId === part.id} onclick={() => selectPart(part.id)}><span class="part-swatch" style={`--accent:${part.accent}`}></span><span>{part.shortName}</span><span class="part-arrow">↗</span></button>{/each}</div></div>
		<p class="prototype-note">SPIKE NOTE · Regions are normalized polygons from a hand-checked vision-model output stub. Requirement matches are intentionally crude keyword filters to prove the interaction, not a compliance claim.</p>
	</section>
</main>

<style>
	:global(body) { margin: 0; background: #02312f; font-family: 'Space Grotesk', sans-serif; }
	:global(button) { font: inherit; }
	.brand-mark { display: grid; height: 34px; width: 34px; place-items: center; border: 1px solid #79f2de; color: #79f2de; font-size: 22px; font-weight: 700; }.brand-name { color: #f0fdfa; font-size: 21px; font-weight: 600; letter-spacing: -.06em; line-height: 1; }.eyebrow, .mono { font-family: 'DM Mono', monospace; }.eyebrow { color: #78bdb2; font-size: 10px; letter-spacing: .13em; }
	h1 { max-width: 700px; color: #f0fdfa; font-size: clamp(2.4rem, 5vw, 5.2rem); font-weight: 500; letter-spacing: -.065em; line-height: .98; margin: 0; }.intro { color: #a7d3cb; font-size: 16px; line-height: 1.6; margin: 18px 0 0; max-width: 620px; }
	.stage-shell, .inspector { border: 1px solid rgba(121,242,222,.28); background: rgba(17,80,75,.32); }.stage-topline, .stage-footer { display: flex; justify-content: space-between; padding: 13px 16px; color: #78bdb2; font: 10px 'DM Mono', monospace; letter-spacing: .08em; }.stage-footer { border-top: 1px solid rgba(121,242,222,.18); font-size: 9px; letter-spacing: .02em; }.stage { height: min(66vw, 650px); min-height: 430px; overflow: hidden; position: relative; background: #0a3e3a; }.stage-grid { position: absolute; inset: 0; opacity: .28; background-image: linear-gradient(rgba(121,242,222,.12) 1px, transparent 1px), linear-gradient(90deg, rgba(121,242,222,.12) 1px, transparent 1px); background-size: 40px 40px; mask-image: linear-gradient(transparent, black 16%, black 84%, transparent); }.paper-stack { position: absolute; inset: 7% 10%; transform: perspective(1100px) rotateX(var(--tilt-x)) rotateY(var(--tilt-y)); transform-style: preserve-3d; transition: transform .18s ease-out; }.paper-shadow { position: absolute; inset: 3% -2% -3% 2%; background: #012421; filter: blur(18px); transform: translateZ(-25px); opacity: .75; pointer-events: none; }.drawing { display: block; height: 100%; width: 100%; object-fit: contain; filter: invert(90%) sepia(25%) saturate(480%) hue-rotate(112deg) brightness(85%); opacity: .88; mix-blend-mode: screen; pointer-events: none; }
	.region { position: absolute; inset: 0; z-index: 2; border: 1px solid transparent; clip-path: polygon(var(--region)); background: color-mix(in srgb, var(--accent) 17%, transparent); cursor: pointer; transition: background .2s, border-color .2s; }.region:hover, .region.selected { background: color-mix(in srgb, var(--accent) 38%, transparent); border-color: var(--accent); }.region-tag { position: absolute; left: 50%; top: 50%; display: grid; height: 26px; width: 26px; place-items: center; border: 1px solid var(--accent); background: #02312f; color: var(--accent); font: 10px 'DM Mono', monospace; transform: translate(-50%, -50%); }.stage-note { position: absolute; bottom: 16px; left: 16px; color: #78bdb2; font: 10px 'DM Mono', monospace; }.live-dot { display: inline-block; height: 6px; width: 6px; border-radius: 50%; background: #27dac2; box-shadow: 0 0 0 4px rgba(39,218,194,.12); margin-right: 8px; }
	.inspector { padding: 22px; }.inspector-kicker { border-bottom: 1px solid rgba(121,242,222,.2); color: #78bdb2; font: 10px 'DM Mono', monospace; letter-spacing: .08em; padding-bottom: 18px; }.selected-heading { display: flex; gap: 14px; padding: 24px 0 20px; }.part-number { display: grid; flex: 0 0 46px; height: 46px; place-items: center; border: 1px solid var(--accent); color: var(--accent); font: 12px 'DM Mono', monospace; }h2 { color: #f0fdfa; font-size: 22px; font-weight: 500; letter-spacing: -.04em; line-height: 1.05; margin: 0; }.selected-heading p { color: #78bdb2; font-size: 12px; line-height: 1.35; margin: 7px 0 0; }.rule-count { align-items: center; border-top: 1px solid rgba(121,242,222,.2); border-bottom: 1px solid rgba(121,242,222,.2); display: flex; gap: 12px; padding: 14px 0; }.rule-count strong { color: #79f2de; font-size: 30px; font-weight: 500; letter-spacing: -.08em; }.rule-count span { color: #a7d3cb; font: 10px 'DM Mono', monospace; line-height: 1.4; }.requirement-list { max-height: 355px; overflow: auto; }.requirement { border-bottom: 1px solid rgba(121,242,222,.13); padding: 15px 0; }.req-meta { color: #78bdb2; display: flex; justify-content: space-between; font: 9px 'DM Mono', monospace; letter-spacing: .02em; }.requirement p { color: #d4eeea; font-size: 12px; line-height: 1.45; margin: 8px 0 0; }.empty { color: #a7d3cb; font-size: 13px; }
	.part-strip { margin-top: 18px; border-top: 1px solid rgba(121,242,222,.28); padding-top: 15px; }.part-buttons { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }.part-buttons button { align-items: center; background: transparent; border: 1px solid rgba(121,242,222,.3); color: #cfe9e4; cursor: pointer; display: flex; gap: 9px; padding: 10px 12px; transition: background .15s, border-color .15s; }.part-buttons button:hover, .part-buttons button.active { background: rgba(121,242,222,.13); border-color: #79f2de; color: #f0fdfa; }.part-swatch { background: var(--accent); height: 7px; width: 7px; }.part-arrow { color: #78bdb2; font-size: 15px; margin-left: 12px; }.prototype-note { color: #609e96; font: 10px 'DM Mono', monospace; line-height: 1.5; margin: 18px 0 0; max-width: 880px; }
	@media (max-width: 640px) { .stage { height: 105vw; min-height: 350px; }.paper-stack { inset: 10% 3%; }.stage-footer span:first-child { max-width: 190px; } }
</style>
