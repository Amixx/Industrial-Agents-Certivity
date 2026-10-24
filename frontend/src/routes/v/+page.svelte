<script lang="ts">
	const variants = [
		['Datasheet', 'Dense hairline-ruled table on mint paper, PDF in a right-hand panel.'],
		['Gazette', 'Editorial newspaper layout with serif headlines.'],
		['Drawing sheet', 'Engineering drawing sheet with title block and ruled frame.'],
		['Workbench', 'Three-pane IDE-style workspace.'],
		['Swiss grid', 'Strict modular grid, large type, minimal colour.'],
		['Card catalogue', 'Requirements as index cards.'],
		['Utility', 'Compact admin-tool look with tabs.'],
		['Audit report', 'Formal report with a summary up front and findings below.'],
		['Instrument panel', 'Dark teal dashboard with mono readouts.'],
		['Reader', 'Single calm column, focused on reading one requirement at a time.']
	];
</script>

<main class="mx-auto max-w-3xl p-6 text-cv-ink-800">
	<p class="text-xs tracking-wide uppercase opacity-60">Certivity</p>
	<h1 class="text-4xl font-semibold">sudo</h1>
	<h2 class="mt-6 mb-3 text-lg font-medium">Variants</h2>
	<ol class="divide-y divide-cv-ink-800/20 border-y border-cv-ink-800/20">
		{#each variants as [name, desc], i}
			{@const n = String(i + 1).padStart(2, '0')}
			<li>
				<a href="/v/{n}" class="flex gap-4 py-3 hover:bg-cv-mint-50">
					<span class="font-mono">{n}</span>
					<span class="font-medium">{name}</span>
					<span class="text-sm opacity-70">{desc}</span>
				</a>
			</li>
		{/each}
	</ol>
</main>
