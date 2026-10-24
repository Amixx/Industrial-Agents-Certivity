declare module 'codemirror-markdown-hybrid' {
	import type { Extension } from '@codemirror/state';
	export function hybridMarkdown(options?: {
		theme?: 'light' | 'dark';
		enablePreview?: boolean;
		enableKeymap?: boolean;
		enableCollapse?: boolean;
	}): Extension;
}
