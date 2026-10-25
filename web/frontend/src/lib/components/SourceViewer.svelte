<script lang="ts">
import Viewer from './PdfViewer.svelte';

let props: {
	url: string;
	page: number;
	highlight?: { paragraph?: string; text?: string } | null;
	label?: string;
	class?: string;
} = $props();
</script>

<Viewer {...props} />
