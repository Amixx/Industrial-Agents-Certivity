<script lang="ts">
import type { Source } from '#lib/api/types.ts';

let {
	source,
	showRegulation = true,
	showParagraph = true,
}: { source: Source; showRegulation?: boolean; showParagraph?: boolean } = $props();
</script>

<span class="inline-flex flex-wrap gap-x-4 text-xs whitespace-nowrap tabular-nums">
	<span>{showRegulation ? `${source.regulation} ` : ''}{source.version}</span>
	<span>Page {source.page}</span>
	{#if showParagraph}
		<span>§ {source.paragraph}</span>
	{/if}
</span>
