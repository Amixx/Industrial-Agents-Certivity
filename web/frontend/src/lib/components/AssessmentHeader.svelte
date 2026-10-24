<script lang="ts">
import type { Snippet } from 'svelte';
import type { Assessment } from '#lib/api/types.ts';
import { formatDate } from '#lib/ui/format.ts';

let { assessment, children }: { assessment: Assessment; children?: Snippet } = $props();
</script>

<div class="ui-grid ui-section items-end pb-4">
	<div class="col-span-3 text-xs">
		<div class="font-bold">Assessment</div>
		<div class="tabular-nums">{formatDate(assessment.createdAt)}</div>
		<div class="tabular-nums">#{assessment.id}</div>
	</div>
	<a
		href="/a/{assessment.id}"
		class="col-span-4 truncate text-4xl leading-none font-bold tracking-tight hover:underline"
	>
		{assessment.caseName ?? 'Untitled spec'}
	</a>
	<div class="col-span-5 flex items-center justify-end gap-3">
		{@render children?.()}
	</div>
</div>
