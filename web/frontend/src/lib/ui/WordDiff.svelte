<script lang="ts">
let { before = '', after = '' }: { before?: string; after?: string } = $props();

type Part = { text: string; kind: 'same' | 'del' | 'ins' };

const parts = $derived.by(() => {
	const a = before.split(/(\s+)/);
	const b = after.split(/(\s+)/);
	const lcs = Array.from({ length: a.length + 1 }, () => new Array<number>(b.length + 1).fill(0));
	for (let i = a.length - 1; i >= 0; i--)
		for (let j = b.length - 1; j >= 0; j--)
			lcs[i][j] = a[i] === b[j] ? lcs[i + 1][j + 1] + 1 : Math.max(lcs[i + 1][j], lcs[i][j + 1]);
	const out: Part[] = [];
	const push = (text: string, kind: Part['kind']) => {
		const last = out.at(-1);
		if (last?.kind === kind) last.text += text;
		else out.push({ text, kind });
	};
	let i = 0;
	let j = 0;
	while (i < a.length && j < b.length) {
		if (a[i] === b[j]) {
			push(a[i++], 'same');
			j++;
		} else if (lcs[i + 1][j] >= lcs[i][j + 1]) push(a[i++], 'del');
		else push(b[j++], 'ins');
	}
	while (i < a.length) push(a[i++], 'del');
	while (j < b.length) push(b[j++], 'ins');
	return out;
});
</script>

<p class="leading-relaxed">
	{#each parts as part, i (i)}
		{#if part.kind === 'del'}
			<del class="text-muted decoration-1">{part.text}</del>
		{:else if part.kind === 'ins'}
			<ins class="bg-mark no-underline">{part.text}</ins>
		{:else}
			{part.text}
		{/if}
	{/each}
</p>
