<script lang="ts">
import type { Snippet } from 'svelte';
import Viewer from './PdfViewer.svelte';

let props: {
	url: string;
	page: number;
	highlight?: { paragraph?: string; text?: string } | null;
	label?: string;
	class?: string;
	children?: Snippet;
} = $props();
</script>

<Viewer {...props} />
