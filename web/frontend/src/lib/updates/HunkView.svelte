<script lang="ts">
import type { Hunk, Segment } from '#lib/api/types.ts';
import { paragraphName } from './run.ts';

let {
	hunk,
	regulation,
	split = false,
	fromVersion,
	toVersion,
	onopen,
	onchange,
}: {
	hunk: Hunk;
	regulation: string;
	split?: boolean;
	fromVersion: string;
	toVersion: string;
	/** Opens the paragraph in the PDF drawer. */
	onopen: () => void;
	/** Scrolls to a requirement change in the impact list. */
	onchange: (id: string) => void;
} = $props();

/** Words of unchanged text kept on each side of an edit inside a long sentence. */
const CONTEXT = 24;

let expanded = $state(false);

/** One line of the diff: a sentence of the old version (−), of the new one (+), or of both. */
type Line = { sign: '-' | '+' | ' '; old?: number; new?: number; segs: Segment[] };
/** A pair for the split view: the old line on the left, the new on the right. */
type Pair = { left?: Line; right?: Line };
type Block = { fold: true; pairs: Pair[] } | { fold: false; pairs: Pair[] };

const blocks = $derived.by(() => {
	let o = 0;
	let n = 0;
	const out: Block[] = [];
	const push = (fold: boolean, pair: Pair) => {
		const last = out.at(-1);
		if (last && last.fold === fold) last.pairs.push(pair);
		else out.push(fold ? { fold: true, pairs: [pair] } : { fold: false, pairs: [pair] });
	};
	for (const row of hunk.rows) {
		const text = row.segments.map(([, t]) => t).join(' ');
		if (row.kind === 'unchanged') {
			const line: Line = { sign: ' ', old: ++o, new: ++n, segs: [['same', text]] };
			push(true, { left: line, right: { ...line } });
		} else if (row.kind === 'amended') {
			push(false, {
				left: { sign: '-', old: ++o, segs: row.segments.filter(([k]) => k !== 'ins') },
				right: { sign: '+', new: ++n, segs: row.segments.filter(([k]) => k !== 'del') },
			});
		} else if (row.kind === 'new')
			push(false, { right: { sign: '+', new: ++n, segs: [['ins', text]] } });
		else push(false, { left: { sign: '-', old: ++o, segs: [['del', text]] } });
	}
	return out;
});

function trim(text: string, at: number, of: number) {
	if (expanded) return text;
	const words = text.split(' ');
	if (words.length <= CONTEXT * 2 + 4) return text;
	if (of === 1) return `${words.slice(0, CONTEXT).join(' ')} … ${words.slice(-CONTEXT).join(' ')}`;
	if (at === 0) return `… ${words.slice(-CONTEXT).join(' ')}`;
	if (at === of - 1) return `${words.slice(0, CONTEXT).join(' ')} …`;
	return `${words.slice(0, CONTEXT).join(' ')} … ${words.slice(-CONTEXT).join(' ')}`;
}

/** A whole new or deleted sentence is one edit; inside an amended one only the edited words are
 * marked. */
const whole = (line: Line) => line.segs.length === 1 && line.segs[0][0] !== 'same';

const statusLabel = $derived(
	hunk.status === 'moved and amended' ? `moved from ${hunk.oldLabel}, amended` : hunk.status,
);
</script>

{#snippet text(line: Line)}
	{#each line.segs as [k, t], i (i)}
		{#if k === 'del' && !whole(line)}
			<del class="rounded-[2px] bg-fg/15 text-muted decoration-1">{t}</del>{' '}
		{:else if k === 'ins' && !whole(line)}
			<ins class="rounded-[2px] bg-mark text-cv-ink-950 no-underline">{t}</ins>{' '}
		{:else if k === 'del'}
			<span class="text-muted line-through decoration-1">{t}</span>
		{:else}
			<span>{k === 'same' ? trim(t, i, line.segs.length) : t}</span>{' '}
		{/if}
	{/each}
{/snippet}

{#snippet cells(line: Line | undefined, numbers: 'both' | 'old' | 'new')}
	{@const tone = line?.sign === '+' ? 'add' : line?.sign === '-' ? 'del' : line ? '' : 'empty'}
	{#if numbers !== 'new'}
		<td class="num {tone}">{line?.old ?? ''}</td>
	{/if}
	{#if numbers !== 'old'}
		<td class="num {tone}">{line?.new ?? ''}</td>
	{/if}
	<td class="sign {tone}">{line?.sign === ' ' ? '' : (line?.sign ?? '')}</td>
	<td class="code {tone}">
		{#if line}
			{@render text(line)}
		{/if}
	</td>
{/snippet}

<article class="mb-6 overflow-hidden rounded-[3px] border border-line-strong" id="hunk-{hunk.id}">
	<header class="flex items-center gap-4 border-b border-line-strong bg-panel px-3 py-1.5">
		<h3 class="font-mono text-[12.5px] tabular-nums">
			<span class="text-muted">{regulation} /</span>
			<span class="font-bold text-fg">{paragraphName(hunk.label)}</span>
		</h3>
		<span class="ui-tag">{statusLabel}</span>
		<span class="font-mono text-[12px] text-muted tabular-nums">p. {hunk.page}</span>
		{#if hunk.heading}
			<span class="truncate text-xs text-muted">{hunk.heading}</span>
		{/if}
		<span class="ml-auto flex shrink-0 items-center gap-3 font-mono text-[12px] tabular-nums">
			<span class="text-accent">+{hunk.addedWords}</span>
			<span class="text-muted">−{hunk.removedWords}</span>
			<span class="flex gap-px" aria-hidden="true">
				{#each Array.from({ length: 5 }, (_, i) => i) as i (i)}
					{@const total = hunk.addedWords + hunk.removedWords || 1}
					{@const adds = Math.round((hunk.addedWords / total) * 5)}
					<span class="size-2 {i < adds ? 'bg-mark' : 'bg-fg/25'}"></span>
				{/each}
			</span>
			<button type="button" class="ui-btn h-7" onclick={onopen}>Open in PDF</button>
		</span>
	</header>

	<table class="diff w-full border-collapse font-mono text-[12.5px] leading-[1.65]">
		{#if split}
			<colgroup>
				<col class="w-11">
				<col class="w-6">
				<col class="w-1/2">
				<col class="w-11">
				<col class="w-6">
				<col class="w-1/2">
			</colgroup>
		{:else}
			<colgroup>
				<col class="w-11">
				<col class="w-11">
				<col class="w-6">
				<col>
			</colgroup>
		{/if}
		<tbody>
			{#each blocks as block, b (b)}
				{#if block.fold && !expanded && block.pairs.length > 1}
					<tr>
						<td colspan={6} class="fold">
							<button
								type="button"
								class="w-full cursor-pointer px-3 py-1 text-left hover:text-fg"
								onclick={() => (expanded = true)}
							>
								@@ {block.pairs.length} unchanged sentences of {paragraphName(hunk.label)} @@
							</button>
						</td>
					</tr>
				{:else if split}
					{#each block.pairs as pair, i (i)}
						<tr>
							{@render cells(pair.left, 'old')}
							{@render cells(pair.right, 'new')}
						</tr>
					{/each}
				{:else}
					{#each block.pairs as pair, i (i)}
						{#if block.fold}
							<tr>
								{@render cells(pair.left, 'both')}
							</tr>
						{:else}
							{#if pair.left}
								<tr>
									{@render cells(pair.left, 'both')}
								</tr>
							{/if}
							{#if pair.right}
								<tr>
									{@render cells(pair.right, 'both')}
								</tr>
							{/if}
						{/if}
					{/each}
				{/if}
			{/each}
		</tbody>
	</table>

	<footer
		class="flex flex-wrap items-baseline gap-x-3 gap-y-1 border-t border-line px-3 py-2 text-xs"
	>
		{#if hunk.changes.length}
			<span class="ui-label">Changes</span>
			{#each hunk.changes as id (id)}
				<button
					type="button"
					class="ui-link cursor-pointer font-mono text-[12px] tabular-nums"
					onclick={() => onchange(id)}
				>
					{id}
				</button>
			{/each}
		{/if}
		{#if hunk.citedBy.length}
			{@const unchanged = hunk.citedBy.filter((id) => !hunk.changes.includes(id))}
			{#if unchanged.length}
				<span class="ui-label">Cited by, wording unchanged</span>
				<span class="font-mono text-[12px] text-muted tabular-nums">
					{unchanged.slice(0, 8).join(', ')}{unchanged.length > 8
						? `, ${unchanged.length - 8} more`
						: ''}
				</span>
			{/if}
		{:else if !hunk.changes.length}
			<span class="text-muted">No requirement of this assessment cites this paragraph.</span>
		{/if}
		<span class="ml-auto font-mono text-[11.5px] text-faint">{fromVersion} to {toVersion}</span>
	</footer>
</article>

<style>
.diff td {
	vertical-align: top;
}
.num {
	padding: 0 8px 0 0;
	text-align: right;
	color: var(--color-faint);
	user-select: none;
	border-right: 1px solid var(--color-line);
}
.sign {
	padding: 0 0 0 8px;
	user-select: none;
	color: var(--color-faint);
}
.code {
	padding: 0 12px 0 4px;
	white-space: pre-wrap;
	overflow-wrap: anywhere;
	font-family: var(--font-grotesk);
	font-size: 13.5px;
}
.add {
	background: color-mix(in srgb, var(--color-mark) 12%, transparent);
}
.sign.add {
	color: var(--color-accent);
	font-weight: 700;
}
.num.add {
	color: var(--color-accent);
	background: color-mix(in srgb, var(--color-mark) 20%, transparent);
}
.del {
	background: color-mix(in srgb, var(--color-fg) 6%, transparent);
}
.sign.del {
	color: var(--color-muted);
	font-weight: 700;
}
.num.del {
	background: color-mix(in srgb, var(--color-fg) 10%, transparent);
}
.empty {
	background: color-mix(in srgb, var(--color-fg) 2.5%, transparent);
}
.fold {
	background: var(--color-select);
	color: var(--color-muted);
	font-size: 12px;
}
</style>
