<script lang="ts">
import spec from '#lib/api/fixtures/spec.md?raw';
import SpecEditor from '#lib/components/SpecEditor.svelte';

let value = $state(spec);
</script>

<main class="grid h-screen grid-cols-2 gap-4 p-4">
	<SpecEditor bind:value class="min-h-0 overflow-auto border" />
	<pre class="min-h-0 overflow-auto border p-2 text-xs">{value}</pre>
</main>
