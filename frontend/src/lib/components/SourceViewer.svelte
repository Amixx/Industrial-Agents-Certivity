<script lang="ts">
import Viewer from './PdfViewer.svelte';

let props: {
	url: string;
	page: number;
	highlight?: { paragraph?: string; text?: string } | null;
	class?: string;
} = $props();
</script>

<Viewer {...props} />
