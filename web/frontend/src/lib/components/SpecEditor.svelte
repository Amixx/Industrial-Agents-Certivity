<script lang="ts">
import { EditorState } from '@codemirror/state';
import { EditorView, placeholder as cmPlaceholder } from '@codemirror/view';
import { hybridMarkdown } from 'codemirror-markdown-hybrid';
import { untrack } from 'svelte';

let {
	value = $bindable(''),
	placeholder = '',
	class: className = '',
}: { value?: string; placeholder?: string; class?: string } = $props();

let host: HTMLDivElement;
let view: EditorView | null = null;

const theme = EditorView.theme({
	'&': { backgroundColor: 'transparent', fontSize: '13px' },
	'&.cm-focused': { outline: 'none' },
	'.cm-content': { fontFamily: 'var(--font-grotesk)', caretColor: '#02312f' },
	'.cm-line.cm-selectedLine, .cm-line.cm-selectedLine *': {
		backgroundColor: '#f0fdfa !important',
		color: '#02312f !important',
	},
	'.cm-placeholder': { color: 'rgb(0 0 0 / 0.4)' },
});

$effect(() => {
	view = new EditorView({
		parent: host,
		state: EditorState.create({
			doc: untrack(() => value),
			extensions: [
				hybridMarkdown({ theme: 'light', enableCollapse: false }),
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
