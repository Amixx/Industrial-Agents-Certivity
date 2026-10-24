<script lang="ts">
	import type { Source } from '#lib/api/types.ts';

	let { source, showRegulation = true }: { source: Source; showRegulation?: boolean } = $props();
</script>

<span class="ui-mono text-[11px] whitespace-nowrap opacity-80">
	{showRegulation ? `${source.regulation} ` : ''}{source.version} · p. {source.page} · § {source.paragraph}
</span>
