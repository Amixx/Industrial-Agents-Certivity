<script lang="ts">
import DOMPurify from 'dompurify';
import { marked } from 'marked';

let { source, class: klass = '' }: { source: string; class?: string } = $props();

const html = $derived(
	typeof document !== 'undefined' ? DOMPurify.sanitize(marked.parse(source, { async: false })) : '',
);
</script>

<div class="md {klass}">{@html html}</div>

<style>
.md {
	font-size: 0.8125rem;
	line-height: 1.5;
}
.md :global(h1) {
	font-size: 1.5rem;
	line-height: 1.1;
	letter-spacing: -0.02em;
	font-weight: 700;
	margin: 0 0 0.75rem;
}
.md :global(h2) {
	font-size: 0.875rem;
	font-weight: 700;
	margin: 1.25rem 0 0.35rem;
	padding-bottom: 0.2rem;
	border-bottom: 1px solid currentColor;
}
.md :global(h3),
.md :global(h4) {
	font-weight: 700;
	margin: 0.9rem 0 0.25rem;
}
.md :global(p) {
	margin: 0.4rem 0;
}
.md :global(ul),
.md :global(ol) {
	margin: 0.4rem 0;
	padding-left: 1.25rem;
}
.md :global(ul) {
	list-style: square;
}
.md :global(ol) {
	list-style: decimal;
}
.md :global(li) {
	margin: 0.1rem 0;
}
.md :global(table) {
	width: 100%;
	border-collapse: collapse;
	margin: 0.6rem 0;
	font-size: 0.75rem;
}
.md :global(th),
.md :global(td) {
	border-bottom: 1px solid rgb(0 0 0 / 0.15);
	padding: 0.3rem 0.75rem 0.3rem 0;
	text-align: left;
	vertical-align: top;
}
.md :global(th) {
	font-weight: 700;
	border-bottom: 2px solid currentColor;
}
.md :global(code) {
	font-size: 0.9em;
	font-weight: 500;
	background: rgb(0 0 0 / 0.06);
	padding: 0 0.2em;
}
.md :global(a) {
	text-decoration: underline;
}
.md :global(blockquote) {
	border-left: 3px solid currentColor;
	padding-left: 0.75rem;
	margin: 0.5rem 0;
	opacity: 0.8;
}
.md :global(hr) {
	margin: 1rem 0;
	border-color: currentColor;
	opacity: 0.3;
}
</style>
