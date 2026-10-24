<script lang="ts">
import type { Snippet } from 'svelte';
import type { Assessment } from '#lib/api/types.ts';
import { formatDate } from '#lib/ui/format.ts';

let { assessment, children }: { assessment: Assessment; children?: Snippet } = $props();
</script>

<div class="ui-rule flex items-center justify-between gap-4 border-b px-4 py-2">
	<div class="flex min-w-0 items-baseline gap-4">
		<a href="/a/{assessment.id}" class="ui-mono truncate text-base font-medium">
			{assessment.caseName ?? 'Untitled spec'}
		</a>
		<span class="ui-mono text-xs opacity-70">{formatDate(assessment.createdAt)}</span>
		<span class="ui-mono text-xs opacity-70">#{assessment.id}</span>
	</div>
	<div class="flex items-center gap-2">
		{@render children?.()}
	</div>
</div>
