<script lang="ts">
// The sub-goal, one step at a time: brain/subgoal aligns two versions of a regulation and finds
// which old requirements change. The example is the challenge's dev pair, UN R175 0.1.0 to
// 1.0.0, around paragraph 5.1.4; texts from subgoal/dev and out/subgoal-dev-det-v6.json, counts
// from brain.subgoal.align on that pair.
import StepControls from './StepControls.svelte';
import StepDetail from './StepDetail.svelte';
import { type Detail, Stepper } from './stepper.svelte.ts';

const OLD_514 =
	'The ACPE shall control acceleration when the vehicle is accelerated from standstill.';
const NEW_514 =
	'The ACPE shall control acceleration when the vehicle is accelerated both from standstill and, as relevant, while creeping.';
const OLD_5141 =
	'If ACPE is not ready to perform an intervention 6 seconds after the initiation of the vehicle powertrain, information of this status shall be indicated to the driver.';
const NEW_5142 =
	'If ACPE is not ready to perform an intervention 6 s after the initiation of the vehicle powertrain, information of this status shall be indicated to the driver.';
const NEW_5141 =
	'An ACPE intervention is not required when: (a) there is an AEBS warning or intervention occurring; or (b) the vehicle speed is greater than 10 km/h.';

const steps: Detail[] = [
	{
		name: 'Old requirements and a new version',
		who: 'Input',
		file: 'subgoal/dev/requirements_old.json',
		desc: 'The requirements written against one version of a regulation, its PDF, and the PDF of a later version. The requirement list of the main engine can be the input here.',
		trace: [
			{
				label: 'R-018, cites 5.1.4',
				body: 'When the vehicle is accelerated from standstill, the ACPE shall control acceleration.',
			},
			{
				label: 'R-019 and R-020, cite 5.1.4.1',
				body: 'Status information when the ACPE is not ready',
			},
			{ label: 'Versions', body: 'UN R175 0.1.0 and 1.0.0' },
		],
	},
	{
		name: 'Parse both versions',
		who: "Code, the main engine's parser",
		file: 'brain/ingest.py, brain/subgoal/text.py',
		desc: 'Both PDFs go through the parser of the main engine and are cut into sentences and list items. Words are compared normalised: case, punctuation, page breaks and units such as "6 seconds" and "6 s" never count as a change.',
		trace: [
			{ label: 'Units', body: '348 in the old version, 391 in the new' },
			{ label: 'Old 5.1.4.1', body: OLD_5141 },
			{ label: 'New 5.1.4.2', body: NEW_5142 },
		],
	},
	{
		name: 'Why not match by number',
		who: 'The trap the alignment avoids',
		file: '',
		desc: 'Old 5.1.4.1 moved to 5.1.4.2, and the new 5.1.4.1 is a different provision. Pairing paragraphs by number would flag two unchanged requirements as modified and miss the new one.',
		trace: [
			{ label: 'Old 5.1.4.1', body: OLD_5141 },
			{ label: 'New 5.1.4.1, a different provision', body: NEW_5141 },
		],
	},
	{
		name: 'Align: exact',
		who: 'Code',
		file: 'brain/subgoal/align.py',
		desc: 'Units with identical normalised words pair up under any label, the same label first. This covers unchanged, renumbered and moved text.',
		trace: [
			{
				label: 'Old 5.1.4.1 and new 5.1.4.2',
				body: 'Identical once normalised: renumbered, not changed',
			},
			{ label: 'On this pair', body: '325 unchanged units' },
		],
	},
	{
		name: 'Align: merged and similar',
		who: 'Code',
		file: 'brain/subgoal/align.py',
		desc: 'A unit that contains two or more units of the other version pairs with all of them, for provisions the PDF glued together. Units still left pair when their wording is at least half the same, and the word diff records the edit.',
		trace: [
			{ label: '5.1.4, old and new', diff: [OLD_514, NEW_514] },
			{ label: 'On this pair', body: '19 amended units' },
		],
	},
	{
		name: 'Leftovers',
		who: 'Code',
		file: 'brain/subgoal/align.py',
		desc: 'A new unit with no partner is new text. An old unit with no partner was deleted.',
		trace: [
			{ label: 'New 5.1.4.1', body: 'No partner in the old version: new' },
			{ label: 'On this pair', body: '47 new units, 4 deleted' },
		],
	},
	{
		name: 'Write the changes',
		who: 'Code',
		file: 'brain/subgoal/changes.py',
		desc: 'Each old requirement follows the units it cites: modified when one was amended, removed when one was deleted, untouched when they only moved. New obligations become added rows. Every row carries its reason and its paragraph in the new PDF.',
		trace: [
			{ label: 'R-018', body: 'Modified: 5.1.4 was amended' },
			{ label: 'R-019, R-020', body: 'Not flagged: renumbered, wording unchanged' },
			{ label: 'New 5.1.4.1', body: 'Added' },
			{ label: 'All 94 old requirements', body: '6 modified, 1 removed, 17 added' },
		],
	},
	{
		name: 'Change list',
		who: 'Output',
		file: 'subgoal-dev.json',
		desc: 'One row per change, with the new text, the reason in plain words and the paragraph to open in the new PDF.',
		trace: [
			{
				label: 'R-018',
				mono: true,
				body: `{
  "change": "modified",
  "new_text": "${NEW_514}",
  "reason": "Paragraph 5.1.4 of UN R175 was amended in version 1.0.0: 'both' was added; 'standstill.' became 'standstill and, as relevant, while creeping.'.",
  "source": { "page": 5, "paragraph": "5.1.4" }
}`,
			},
		],
	},
];

const st = new Stepper(steps.length, { loop: true });
const step = $derived(st.step);
const cur = $derived(steps[st.step]);

// Step indices where each part of the picture appears.
const PARSE = 1;
const TRAP = 2;
const EXACT = 3;
const SIMILAR = 4;
const LEFT = 5;
const WRITE = 6;

// Paragraph boxes: x, version row, label, a short excerpt.
const W = 300;
const H = 78;
const OLD_Y = 70;
const NEW_Y = 222;
const boxes = [
	{ id: 'o514', x: 180, y: OLD_Y, label: '5.1.4', text: OLD_514 },
	{ id: 'o5141', x: 530, y: OLD_Y, label: '5.1.4.1', text: OLD_5141 },
	{ id: 'n514', x: 180, y: NEW_Y, label: '5.1.4', text: NEW_514 },
	{ id: 'n5141', x: 530, y: NEW_Y, label: '5.1.4.1', text: NEW_5141 },
	{ id: 'n5142', x: 880, y: NEW_Y, label: '5.1.4.2', text: NEW_5142 },
];
const mid = (x: number) => x + W / 2;

// Which box the current step is about, for the highlight.
const focus: Record<number, string[]> = {
	[TRAP]: ['o5141', 'n5141'],
	[EXACT]: ['o5141', 'n5142'],
	[SIMILAR]: ['o514', 'n514'],
	[LEFT]: ['n5141'],
};
</script>

<!-- Arrow keys step through the stages once any control inside has focus. -->
<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
<figure
	class="change"
	aria-label="Regulation change diagram, arrow keys step through the stages"
	onkeydown={st.key}
	use:st.autoplay
>
	<StepControls {st} caption="UN R175, 0.1.0 to 1.0.0" />

	<div class="mt-6 overflow-x-auto pb-2">
		<svg
			viewBox="0 0 1200 350"
			class="w-full min-w-[960px]"
			role="img"
			aria-labelledby="change-title"
		>
			<title id="change-title">
				Old paragraphs 5.1.4 and 5.1.4.1 of UN R175 aligned with new 5.1.4, 5.1.4.1 and 5.1.4.2.
			</title>

			<text x="0" y={OLD_Y + 44} class="row-label">0.1.0</text>
			<text x="0" y={OLD_Y + 62} class="row-sub">old version</text>
			<text x="0" y={NEW_Y + 44} class="row-label">1.0.0</text>
			<text x="0" y={NEW_Y + 62} class="row-sub">new version</text>
			<line x1="160" x2="1200" y1={OLD_Y + H / 2} y2={OLD_Y + H / 2} class="rail" />
			<line x1="160" x2="1200" y1={NEW_Y + H / 2} y2={NEW_Y + H / 2} class="rail" />

			<!-- Old requirements, pinned to the paragraphs they cite. -->
			{#each [
				{ id: 'R-018', x: 180, state: 'modified' },
				{ id: 'R-019', x: 530, state: 'unchanged' },
				{ id: 'R-020', x: 620, state: 'unchanged' },
			] as r}
				{@const done = step >= WRITE}
				<g class="req {done ? r.state : ''}">
					<rect x={r.x} y="14" width="80" height="26" rx="3" />
					<text x={r.x + 40} y="32" text-anchor="middle">{r.id}</text>
					<line x1={r.x + 40} x2={r.x + 40} y1="40" y2={OLD_Y} class="pin" />
				</g>
				{#if done}
					<text x={r.x + 88} y="32" class="verdict {r.state}">
						{r.state === 'modified' ? 'modified' : r.id === 'R-020' ? 'unchanged' : ''}
					</text>
				{/if}
			{/each}

			<!-- The trap: pairing by number. -->
			<g class="link trap" class:show={step === TRAP}>
				<line x1={mid(530)} x2={mid(530)} y1={OLD_Y + H} y2={NEW_Y} />
				<text x={mid(530) + 10} y={(OLD_Y + H + NEW_Y) / 2 + 5}>
					same number, different provision
				</text>
			</g>

			<!-- Exact pass: renumbered, unchanged. -->
			<g class="link exact" class:show={step >= EXACT}>
				<line x1={mid(530)} x2={mid(880)} y1={OLD_Y + H} y2={NEW_Y} pathLength="1" />
				<text x="870" y="172">identical, renumbered</text>
			</g>

			<!-- Similar pass: amended. -->
			<g class="link similar" class:show={step >= SIMILAR}>
				<line x1={mid(180)} x2={mid(180)} y1={OLD_Y + H} y2={NEW_Y} pathLength="1" />
				<text x={mid(180) + 10} y={(OLD_Y + H + NEW_Y) / 2 + 5}>amended</text>
			</g>

			{#each boxes as b}
				{@const on = focus[step]?.includes(b.id)}
				{@const fresh = b.id === 'n5141' && step >= LEFT}
				<g class="box" class:show={step >= PARSE} class:on class:fresh>
					<rect x={b.x} y={b.y} width={W} height={H} rx="3" />
					<foreignObject x={b.x + 10} y={b.y + 6} width={W - 20} height={H - 10}>
						<div class="box-text">
							<span class="box-label">{b.label}</span>
							{b.text}
						</div>
					</foreignObject>
				</g>
			{/each}

			<g class="added" class:show={step >= LEFT}>
				<text x={mid(530)} y={NEW_Y + H + 26} text-anchor="middle">
					{step >= WRITE ? 'added row' : 'no partner: new'}
				</text>
			</g>
		</svg>
	</div>

	<StepDetail {step} {cur} title={step === 0 ? 'The case' : 'Around paragraph 5.1.4'} />
</figure>

<style>
text {
	font-family: var(--font-mono);
	font-size: 13px;
	fill: var(--color-faint);
}
.row-label {
	font-family: var(--font-display);
	font-size: 30px;
	fill: var(--color-accent);
}
text.row-sub {
	font-size: 11.5px;
	letter-spacing: 0.08em;
	text-transform: uppercase;
	fill: var(--color-muted);
}
.rail {
	stroke: var(--color-line);
	stroke-width: 1;
}
.box {
	opacity: 0;
	transform: translateY(8px);
	transition:
		opacity 400ms ease,
		transform 400ms cubic-bezier(0.2, 0.7, 0.2, 1);
}
.box.show {
	opacity: 1;
	transform: none;
}
.box rect {
	fill: var(--color-panel);
	stroke: var(--color-line-strong);
	stroke-width: 1;
	transition: stroke 300ms;
}
.box-text {
	display: -webkit-box;
	-webkit-line-clamp: 3;
	line-clamp: 3;
	-webkit-box-orient: vertical;
	overflow: hidden;
	font-size: 13px;
	line-height: 1.4;
	color: var(--color-fg);
}
.box-label {
	margin-right: 0.4rem;
	font-family: var(--font-mono);
	font-weight: 600;
	color: var(--color-accent);
}
.req rect {
	fill: none;
	stroke: var(--color-line-strong);
	transition:
		fill 300ms,
		stroke 300ms;
}
.req text {
	fill: var(--color-fg);
}
.req .pin {
	stroke: var(--color-line-strong);
}
text.verdict.modified {
	fill: var(--color-accent);
}
.link {
	opacity: 0;
	transition: opacity 400ms ease;
}
.link.show {
	opacity: 1;
}
.link line {
	stroke-width: 2;
	stroke-dasharray: 1;
	stroke-dashoffset: 1;
	transition: stroke-dashoffset 600ms cubic-bezier(0.4, 0, 0.2, 1);
}
.exact line {
	stroke: var(--color-mark);
}
.similar line {
	stroke: var(--color-accent);
}
g.similar text,
g.exact text {
	fill: var(--color-fg);
}
.trap line {
	stroke: var(--color-faint);
	stroke-dasharray: 6 5;
	stroke-dashoffset: 0;
}
.added {
	opacity: 0;
	transition: opacity 400ms ease;
}
.added.show {
	opacity: 1;
}
g.added text {
	fill: var(--color-accent);
}

/* State rules last, so they win over the base rules above. */
.box.on rect {
	stroke: var(--color-accent);
	stroke-width: 2;
}
.box.fresh rect {
	stroke: var(--color-accent);
	stroke-dasharray: 5 4;
}
.req.modified rect {
	fill: var(--color-accent);
	stroke: var(--color-accent);
}
.req.modified text {
	fill: var(--color-on-accent);
}
.req.unchanged rect {
	stroke-dasharray: 3 3;
}
.req.unchanged text {
	fill: var(--color-faint);
}
.link.show line {
	stroke-dashoffset: 0;
}

@media (prefers-reduced-motion: reduce) {
	.box,
	.link,
	.link line,
	.added,
	.box rect,
	.req rect {
		transition: none;
	}
}
</style>
