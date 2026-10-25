<script lang="ts">
import { EditorState } from '@codemirror/state';
import { placeholder as cmPlaceholder, EditorView } from '@codemirror/view';
import { hybridMarkdown } from 'codemirror-markdown-hybrid';
import { untrack } from 'svelte';
import { colorScheme } from '#lib/ui/colorScheme.svelte.ts';

let {
	value = $bindable(''),
	placeholder = '',
	class: className = '',
}: { value?: string; placeholder?: string; class?: string } = $props();

let host: HTMLDivElement;
let view: EditorView | null = null;

const theme = EditorView.theme({
	'&': { backgroundColor: 'transparent !important', fontSize: '13px' },
	'th, td': { borderColor: 'var(--color-line-strong) !important' },
	th: { backgroundColor: 'var(--color-select) !important', color: 'var(--color-fg) !important' },
	'&.cm-focused': { outline: 'none' },
	'.cm-content': { fontFamily: 'var(--font-grotesk)', caretColor: 'var(--color-mark)' },
	'.cm-line.cm-selectedLine, .cm-line.cm-selectedLine *': {
		backgroundColor: 'var(--color-select) !important',
		color: 'var(--color-fg) !important',
	},
	'.cm-placeholder': { color: 'var(--color-faint)' },
});

$effect(() => {
	view = new EditorView({
		parent: host,
		state: EditorState.create({
			doc: untrack(() => value),
			extensions: [
				hybridMarkdown({ theme: colorScheme.current, enableCollapse: false }),
				theme,
				EditorView.lineWrapping,
				cmPlaceholder(untrack(() => placeholder)),
				EditorView.updateListener.of((u) => {
					if (u.docChanged) value = u.state.doc.toString();
				}),
			],
		}),
	});
	return () => {
		view?.destroy();
		view = null;
	};
});

$effect(() => {
	if (view && value !== view.state.doc.toString()) {
		view.dispatch({ changes: { from: 0, to: view.state.doc.length, insert: value } });
	}
});
</script>

<div bind:this={host} class={className}></div>
