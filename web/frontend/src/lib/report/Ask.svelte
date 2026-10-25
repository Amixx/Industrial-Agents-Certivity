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
type Place = { left: number; top: number; width: number; above: boolean; maxHeight: number };
type RecognitionWindow = {
	SpeechRecognition?: new () => Recognition;
	webkitSpeechRecognition?: new () => Recognition;
};

const SELECTION_LIMIT = 6000;
const POPUP_WIDTH = 416;
const GUTTER = 16;

const byId = $derived(new Map(requirements.map((r) => [r.id, r])));

let SpeechInput = $state<(new () => Recognition) | undefined>();
/** The floating "Ask" button, in page coordinates, while report text is selected. */
let anchor = $state<{ x: number; y: number; text: string; rect: DOMRect } | null>(null);
/** The selected text the open popup asks about; empty while the popup is closed. */
let selection = $state('');
/** Where the popup sits, in page coordinates. Above the selection it grows upward from `top`. */
let place = $state<Place>({ left: 0, top: 0, width: POPUP_WIDTH, above: false, maxHeight: 0 });
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
	anchor = { x: rect.left + rect.width / 2 + scrollX, y: rect.bottom + scrollY + 8, text, rect };
}

/** Below the selection when it sits in the upper half of the viewport, above it otherwise. */
function placeAt(rect: DOMRect) {
	const width = Math.min(POPUP_WIDTH, innerWidth - 2 * GUTTER);
	const centre = rect.left + rect.width / 2;
	const left = Math.min(Math.max(centre - width / 2, GUTTER), innerWidth - width - GUTTER);
	const above = rect.top + rect.height / 2 > innerHeight / 2;
	const room = above ? rect.top - GUTTER - 8 : innerHeight - rect.bottom - GUTTER - 8;
	place = {
		left: left + scrollX,
		top: (above ? rect.top - 8 : rect.bottom + 8) + scrollY,
		width,
		above,
		maxHeight: Math.max(room, 240),
	};
}

function open() {
	if (!anchor) return;
	placeAt(anchor.rect);
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

<svelte:document
	onmouseup={onSelect}
	onkeyup={(e) => (e.key === 'Escape' && selection ? close() : onSelect())}
/>

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
	<aside
		class="popup"
		class:above={place.above}
		aria-label="Ask about the selection"
		style="left: {place.left}px; top: {place.top}px; width: {place.width}px; max-height: {place.maxHeight}px"
	>
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
	border-radius: 3px;
	cursor: pointer;
}
.float:hover {
	background: var(--color-cv-ink-800);
}
/* Corners grow with the element: 6px on the popup, 3px on its controls, 2px on cite chips. */
.popup {
	position: absolute;
	z-index: 20;
	overflow-y: auto;
	background: white;
	border: 1px solid rgb(0 0 0 / 0.16);
	border-radius: 6px;
	font-size: 0.9rem;
}
.popup.above {
	transform: translateY(-100%);
}
.inner {
	padding: 0.875rem 1.125rem 1.125rem;
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
	flex-wrap: wrap;
	gap: 0.5rem;
	margin-top: 0.75rem;
}
input {
	flex: 1;
	min-width: 10rem;
	height: 2.25rem;
	padding: 0 0.6rem;
	border: 1px solid rgb(0 0 0 / 0.3);
	border-radius: 3px;
}
input:focus {
	border-color: black;
	outline: none;
}
form button {
	height: 2.25rem;
	padding: 0 0.9rem;
	background: black;
	color: white;
	font-weight: 700;
	border-radius: 3px;
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
	border-radius: 2px;
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
	.popup {
		display: none;
	}
}
</style>
