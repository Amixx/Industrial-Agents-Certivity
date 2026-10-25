<script lang="ts">
import WordDiff from '#lib/ui/WordDiff.svelte';
import { type Detail, pad } from './stepper.svelte.ts';

// The panel under a step-through diagram: what the current step does, and the traced example.
let { step, cur, title }: { step: number; cur: Detail; title: string } = $props();
</script>

<div class="mt-6 grid gap-6 border-t border-line pt-6 md:grid-cols-12">
	<div class="md:col-span-5">
		<span class="ui-label">{pad(step + 1)}, {cur.who}</span>
		<h3 class="ui-display mt-2 text-[2rem]">{cur.name}</h3>
		<p class="mt-3 max-w-[52ch] leading-relaxed text-muted">{cur.desc}</p>
		{#if cur.file}
			<p class="ui-label mt-4 normal-case tracking-normal text-faint">{cur.file}</p>
		{/if}
	</div>
	<div class="ui-panel p-5 md:col-span-7">
		<span class="ui-label">{title}</span>
		{#key step}
			<dl class="trace mt-3 space-y-3">
				{#each cur.trace as r}
					<div>
						<dt class="ui-label text-faint">{r.label}</dt>
						<dd class="mt-1 leading-relaxed">
							{#if r.diff}
								<WordDiff before={r.diff[0]} after={r.diff[1]} />
							{:else if Array.isArray(r.body)}
								<ol class="list-decimal space-y-1 pl-5">
									{#each r.body as q}
										<li>{q}</li>
									{/each}
								</ol>
							{:else if r.mono}
								<pre
									class="overflow-x-auto font-mono text-[13px] whitespace-pre-wrap"
								>{r.body}</pre>
							{:else}
								{r.body}
							{/if}
						</dd>
					</div>
				{/each}
			</dl>
		{/key}
	</div>
</div>

<style>
.trace {
	animation: trace-in 350ms cubic-bezier(0.2, 0.7, 0.2, 1);
}
@keyframes trace-in {
	from {
		opacity: 0;
		transform: translateY(0.5rem);
	}
}
@media (prefers-reduced-motion: reduce) {
	.trace {
		animation: none;
	}
}
</style>
