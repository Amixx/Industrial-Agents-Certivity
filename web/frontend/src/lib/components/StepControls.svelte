<script lang="ts">
import { pad, type Stepper } from './stepper.svelte.ts';

let { st, caption = '' }: { st: Stepper; caption?: string } = $props();
</script>

<div class="flex flex-wrap items-center gap-2">
	<button type="button" class="ui-btn ui-btn-primary w-20 justify-center" onclick={st.toggle}>
		{st.playing ? 'Pause' : st.step === st.last && !st.loop ? 'Replay' : 'Play'}
	</button>
	<button
		type="button"
		class="ui-btn"
		onclick={() => st.pick(st.step - 1)}
		disabled={st.step === 0}
	>
		Previous
	</button>
	<button type="button" class="ui-btn" onclick={st.next} disabled={st.step === st.last && !st.loop}>
		Next
	</button>
	<span class="ui-label ml-3 tabular-nums">{pad(st.step + 1)} / {pad(st.last + 1)}</span>
	{#if caption}
		<span class="ui-label ml-auto hidden sm:block">{caption}</span>
	{/if}
</div>
