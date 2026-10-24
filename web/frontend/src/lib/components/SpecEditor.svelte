<script lang="ts">
import { EditorState } from '@codemirror/state';
import { EditorView } from '@codemirror/view';
import { hybridMarkdown } from 'codemirror-markdown-hybrid';
import { untrack } from 'svelte';

let { value = $bindable(''), class: className = '' }: { value?: string; class?: string } = $props();

let host: HTMLDivElement;
let view: EditorView | null = null;

$effect(() => {
	view = new EditorView({
		parent: host,
		state: EditorState.create({
			doc: untrack(() => value),
			extensions: [
				hybridMarkdown({ theme: 'light', enableCollapse: false }),
				EditorView.lineWrapping,
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
