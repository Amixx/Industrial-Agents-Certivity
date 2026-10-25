<script lang="ts">
import { onMount } from 'svelte';
import { api } from '#lib/api/client.ts';
import type { AskAnswer, Requirement } from '#lib/api/types.ts';
import { citeLabel } from './cite.ts';

let { requirements }: { requirements: Requirement[] } = $props();

type Recognition = {
	lang: string;
	interimResults: boolean;
	onresult:
		| ((e: {
				results: ArrayLike<ArrayLike<{ transcript: string }> & { isFinal: boolean }>;
		  }) => void)
		| null;
	onend: (() => void) | null;
	onerror: ((e: { error: string }) => void) | null;
	start(): void;
	stop(): void;
};
type RecognitionWindow = {
	SpeechRecognition?: new () => Recognition;
	webkitSpeechRecognition?: new () => Recognition;
};

const SELECTION_LIMIT = 6000;

const byId = $derived(new Map(requirements.map((r) => [r.id, r])));

let SpeechInput = $state<(new () => Recognition) | undefined>();
/** The floating "Ask" button, in page coordinates, while report text is selected. */
let anchor = $state<{ x: number; y: number; text: string } | null>(null);
/** The selected text the open panel asks about; empty while the panel is closed. */
let selection = $state('');
let question = $state('');
let answer = $state<AskAnswer | null>(null);
let error = $state('');
let asking = $state(false);
let listening = $state(false);
let speaking = $state(false);
let recognition: Recognition | null = null;

onMount(() => {
	const w = window as unknown as RecognitionWindow;
	SpeechInput = w.SpeechRecognition ?? w.webkitSpeechRecognition;
	return () => {
		recognition?.stop();
		speechSynthesis.cancel();
	};
});

function onSelect() {
	const sel = window.getSelection();
	const text = sel?.toString().trim() ?? '';
	if (!sel || !text || sel.rangeCount === 0) {
		anchor = null;
		return;
	}
	const range = sel.getRangeAt(0);
	const node = range.commonAncestorContainer;
	const el = node instanceof Element ? node : node.parentElement;
	if (!el?.closest('.report')) {
		anchor = null;
		return;
	}
	const rect = range.getBoundingClientRect();
	anchor = { x: rect.left + rect.width / 2 + scrollX, y: rect.bottom + scrollY + 8, text };
}

function open() {
	if (!anchor) return;
	selection = anchor.text.slice(0, SELECTION_LIMIT);
	anchor = null;
	window.getSelection()?.removeAllRanges();
	question = '';
	answer = null;
	error = '';
}

function close() {
	recognition?.stop();
	stopSpeaking();
	selection = '';
}

function listen() {
	if (!SpeechInput) return;
	stopSpeaking();
	question = '';
	error = '';
	recognition = new SpeechInput();
	recognition.lang = 'en-US';
	recognition.interimResults = true;
	recognition.onresult = (e) => {
		question = Array.from(e.results, (r) => r[0].transcript).join('');
	};
	recognition.onerror = (e) => {
		error = `Speech input stopped: ${e.error}`;
	};
	recognition.onend = () => {
		listening = false;
		if (question.trim() && !error) submit(true);
	};
	recognition.start();
	listening = true;
}

async function submit(spoken: boolean) {
	if (!question.trim() || asking) return;
	asking = true;
	error = '';
	answer = null;
	try {
		answer = await api.ask(question.trim(), selection, requirements);
		if (spoken) speak();
	} catch (e) {
		error = e instanceof Error ? e.message : String(e);
	} finally {
		asking = false;
	}
}

function speak() {
	if (!answer) return;
	speechSynthesis.cancel();
	const utterance = new SpeechSynthesisUtterance(answer.sentences.map((s) => s.text).join(' '));
	utterance.lang = 'en-US';
	utterance.onend = () => {
		speaking = false;
	};
	speaking = true;
	speechSynthesis.speak(utterance);
}

function stopSpeaking() {
	speechSynthesis.cancel();
	speaking = false;
}

function usd(value: number) {
	return `$${value.toFixed(value < 0.1 ? 4 : 2)}`;
}
</script>

<svelte:document onmouseup={onSelect} onkeyup={onSelect} />

{#if anchor}
	<button
		type="button"
		class="float"
		style="left: {anchor.x}px; top: {anchor.y}px"
		onmousedown={(e) => e.preventDefault()}
		onclick={open}
	>
		Ask about this
	</button>
{/if}

{#if selection}
	<aside class="panel" aria-label="Ask about the selection">
		<div class="inner">
			<div class="head">
				<p class="label">Asking about</p>
				<button type="button" class="link" onclick={close}>Close</button>
			</div>
			<blockquote>
				{selection.length > 280 ? `${selection.slice(0, 280)}…` : selection}
			</blockquote>
			<form
				onsubmit={(e) => {
					e.preventDefault();
					submit(false);
				}}
			>
				{#if SpeechInput}
					<button
						type="button"
						class="mic"
						class:on={listening}
						disabled={asking}
						onclick={() => (listening ? recognition?.stop() : listen())}
					>
						{listening ? 'Listening, click to stop' : 'Speak'}
					</button>
				{/if}
				<input
					bind:value={question}
					placeholder={SpeechInput ? 'Or type a question' : 'Type a question'}
					aria-label="Question"
				>
				<button type="submit" disabled={asking || !question.trim()}>Ask</button>
			</form>
			{#if asking}
				<p class="status">Answering…</p>
			{:else if error}
				<p class="status">{error}</p>
			{:else if answer}
				<p class="answer">
					{#each answer.sentences as sentence, i (i)}
						{sentence.text}
						{#each sentence.cites as id (id)}
							{@const req = byId.get(id)}
							{#if req}
								<a
									class="cite"
									href="#req-{id}"
									title="{req.source.regulation}, page {req.source.page}"
									>{citeLabel(req)}</a
								>
							{/if}
						{/each}
						{' '}
					{/each}
				</p>
				<p class="meta">
					<button type="button" class="link" onclick={speaking ? stopSpeaking : speak}>
						{speaking ? 'Stop reading' : 'Read aloud'}
					</button>
					<span>
						This answer cost {usd(answer.costUsd)}. Spent {usd(answer.spentUsd)} of
						{usd(answer.budgetUsd)}.
					</span>
				</p>
			{/if}
		</div>
	</aside>
{/if}

<style>
.float {
	position: absolute;
	z-index: 15;
	transform: translateX(-50%);
	padding: 0.35rem 0.6rem;
	background: black;
	color: white;
	font-size: 0.8rem;
	font-weight: 700;
	border-radius: var(--radius-button);
	cursor: pointer;
}
.float:hover {
	background: var(--color-cv-ink-800);
}
.panel {
	position: fixed;
	right: 0;
	bottom: 0;
	left: 0;
	z-index: 20;
	max-height: 50vh;
	overflow-y: auto;
	background: white;
	border-top: 1.5pt solid black;
	font-size: 0.9rem;
}
.inner {
	max-width: 210mm;
	margin: 0 auto;
	padding: 1rem 16mm 1.25rem;
}
.head {
	display: flex;
	justify-content: space-between;
	align-items: baseline;
}
.label {
	font-size: 0.75rem;
	font-weight: 700;
}
blockquote {
	margin-top: 0.4rem;
	padding-left: 0.75rem;
	border-left: 1.5pt solid var(--color-cv-mint-300);
	font-size: 0.85rem;
	line-height: 1.4;
	color: var(--color-cv-ink-800);
}
form {
	display: flex;
	gap: 0.5rem;
	margin-top: 0.75rem;
}
input {
	flex: 1;
	height: 2.25rem;
	padding: 0 0.6rem;
	border: 1px solid black;
	border-radius: var(--radius-control);
}
form button {
	height: 2.25rem;
	padding: 0 0.9rem;
	background: black;
	color: white;
	font-weight: 700;
	border-radius: var(--radius-button);
	cursor: pointer;
}
form button:disabled {
	opacity: 0.4;
	cursor: default;
}
.mic.on {
	background: var(--color-cv-mint-300);
	color: black;
}
.status {
	margin-top: 0.75rem;
	color: var(--color-cv-ink-800);
}
.answer {
	margin-top: 0.75rem;
	font-size: 1rem;
	line-height: 1.6;
}
.cite {
	display: inline-block;
	margin-left: 0.2rem;
	padding: 0 0.2rem;
	border: 0.5pt solid currentColor;
	border-radius: var(--radius-control);
	font-size: 0.7rem;
	font-weight: 600;
	line-height: 1.5;
	vertical-align: 0.15em;
	white-space: nowrap;
	color: var(--color-cv-teal-700);
}
.cite:hover {
	background: var(--color-cv-mint-300);
	border-color: var(--color-cv-mint-300);
	color: black;
}
.meta {
	display: flex;
	flex-wrap: wrap;
	gap: 0 1rem;
	margin-top: 0.5rem;
	font-size: 0.75rem;
	color: var(--color-cv-ink-800);
}
.link {
	font-weight: 700;
	text-decoration: underline;
	text-underline-offset: 2px;
	cursor: pointer;
}

@media print {
	.float,
	.panel {
		display: none;
	}
}
</style>
