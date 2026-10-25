<script lang="ts">
// The engine's data flow, one step at a time: the stages of brain/pipeline.py on a model lane
// and a code lane, with one real paragraph (UN R42 6.1.1, front bumper run) traced through each.
// Counts and texts come from out/heldout-api.json and its log.

type Row = { label: string; body: string | string[]; mono?: boolean };
type Step = {
	name: string;
	who: string;
	file: string;
	desc: string;
	trace: Row[];
	// Node on each lane, with a tag when someone other than the usual worker does it;
	// undefined means the lane is not used.
	model?: string;
	code?: string;
	count?: string;
	unit?: string;
};

const steps: Step[] = [
	{
		name: 'Spec and exploded view',
		who: 'Input',
		file: 'cases/heldout-front-bumper/spec.md',
		desc: 'A product specification in Markdown and, when there is one, the exploded-view image.',
		trace: [
			{
				label: 'spec.md',
				body: 'Bumper (front): exterior body/trim module combining fascia, energy-management structure, and integrated sensing, lighting, and electronics.',
			},
			{ label: 'Vehicle category', body: 'M1, passenger car' },
		],
	},
	{
		name: 'Parse',
		who: 'Code, once per corpus',
		file: 'brain/ingest.py',
		desc: 'Each regulation PDF becomes a tree of numbered paragraphs, each with its page and label. From here on the parser owns the citation: no model ever writes a page number.',
		code: '',
		count: '56',
		unit: 'regulations',
		trace: [
			{
				label: 'UN R42, page 3',
				body: '6.1.1 The lighting and signalling devices shall continue to operate correctly and to remain visible. Should the adjustment of the factory-fitted lighting devices be disturbed, it may be corrected to conform to the required specifications, provided this can be done by the normal means of adjustment. Bulbs may be replaced in the event of filament failure.',
			},
			{ label: 'Record', body: 'UN R42 | 0.2.0 | 6.1.1, page 3', mono: true },
		],
	},
	{
		name: 'Product profile',
		who: 'Model',
		file: 'brain/profile.py',
		desc: 'The model reads the spec and the exploded view and lists the parts, functions, vehicle category and electronics. Negated features such as "without radar" do not count.',
		model: '',
		count: '55',
		unit: 'terms',
		trace: [
			{
				label: 'Product',
				body: 'Front bumper module: fascia, absorber, lower stiffener, integrated sensing, lighting and electronics',
			},
			{ label: 'Category', body: 'M1' },
			{ label: 'Electronics', body: 'Yes' },
		],
	},
	{
		name: 'Regulation pick',
		who: 'Code ranks, model reviews, a person can override',
		file: 'brain/select_regs.py',
		desc: 'Code ranks all 56 regulations by matching product terms against titles, scopes and definitions. The model reviews each scope card and keeps the ones that apply. A reviewer can force a regulation in or out.',
		model: '',
		code: 'reviewer',
		count: '7',
		unit: 'regulations',
		trace: [
			{ label: 'UN R42', body: 'Front and rear protective devices' },
			{ label: 'Verdict', body: 'Kept, probability 0.75' },
			{ label: 'Also kept', body: 'UN R10, R26, R48, R127, R148, GTR 9' },
		],
	},
	{
		name: 'Reference graph',
		who: 'Code',
		file: 'brain/graph.py',
		desc: 'Regular expressions link each paragraph to its parent, to the paragraphs and annexes it cites, and to the definitions it uses. Later stages read a paragraph together with this context.',
		code: '',
		trace: [
			{
				label: 'Parent, 6.1',
				body: 'After each impact test made in accordance with the conditions and procedure specified in annex 3 to this Regulation, the vehicle shall meet the following requirements:',
			},
			{ label: 'Cites', body: 'Annex 3, the impact test conditions and procedure' },
		],
	},
	{
		name: 'Paragraph screening',
		who: 'Jev answers, code combines',
		file: 'brain/jev.py',
		desc: "Jev, TypeSafe's decision model, answers five yes/no questions about every candidate paragraph with a calibrated probability. A logistic regression turns the five answers into the chance that an expert cites the paragraph.",
		model: 'Jev',
		code: '',
		count: '3,240',
		unit: 'scored',
		trace: [
			{
				label: 'Five questions',
				body: [
					'Does it state a technical requirement or test condition?',
					'Is it about a function the product has?',
					'Is it about a function the product lacks?',
					'Is it about installation on the vehicle?',
					'Is it about electromagnetic compatibility?',
				],
			},
		],
	},
	{
		name: 'Relevance ranking',
		who: 'Model scores, code cuts',
		file: 'brain/relevance.py',
		desc: "The model reads every candidate in document order, with its heading path and parent clause, and estimates whether an expert would cite it. Its score is blended with Jev's, and each regulation keeps the paragraphs that reach 0.2 times its own best.",
		model: '',
		code: '',
		count: '476',
		unit: 'paragraphs',
		trace: [
			{ label: 'Blended score', body: '0.55' },
			{ label: 'Result', body: 'Kept, one of 476 paragraphs' },
		],
	},
	{
		name: 'Obligation drafts',
		who: 'Model',
		file: 'brain/rewrite.py',
		desc: "Each kept paragraph becomes standalone obligations in EARS form, one per row. Each row keeps the numbers and carries the parent clause's condition.",
		model: '',
		count: '840',
		unit: 'drafts',
		trace: [
			{
				label: 'Row 1 quotes',
				body: 'The lighting and signalling devices shall continue to operate correctly and to remain visible.',
			},
			{
				label: 'Row 2 quotes',
				body: 'Should the adjustment of the factory-fitted lighting devices be disturbed, it may be corrected to conform to the required specifications, provided this can be done by the normal means of adjustment.',
			},
		],
	},
	{
		name: 'Verify',
		who: 'Code',
		file: 'brain/verify.py',
		desc: 'Every number in a draft must appear in its source paragraph or an ancestor, every citation must point at the base version, and duplicates go. Drafts that fail are dropped.',
		code: '',
		count: '810',
		unit: 'drafts',
		trace: [
			{ label: 'Numbers', body: 'None to check' },
			{ label: 'Version', body: '0.2.0, the base version' },
			{ label: 'Result', body: 'Both rows pass' },
		],
	},
	{
		name: 'Expert-likeness cut',
		who: 'Model scores, code applies the cut and the rules',
		file: 'brain/sections.py, brain/boilerplate.py',
		desc: 'The model scores whether an expert would list each draft and how central its section is. A row stays when the product of the two reaches 0.15. Rules drop rows that only point elsewhere or spell out the approval mark, and a row whose quote is its own takes that exact sentence as its text.',
		model: '',
		code: '',
		count: '601',
		unit: 'rows',
		trace: [
			{ label: 'Result', body: 'Both rows kept' },
			{ label: 'Text', body: 'Set to the exact source sentence' },
		],
	},
	{
		name: 'Consolidation',
		who: 'Model decides, code collapses',
		file: 'brain/consolidate.py',
		desc: 'For each list paragraph the model decides whether its items are one obligation or several. Code collapses rows that share a quote, drops exact duplicates and keeps every row under 2,000 characters.',
		model: '',
		code: '',
		count: '550',
		unit: 'rows',
		trace: [{ label: '6.1.1', body: 'Two separate obligations, so two rows' }],
	},
	{
		name: 'Cited requirements',
		who: 'Output',
		file: 'requirements.json',
		desc: 'One row per obligation. Each cites the regulation, base version, page and paragraph, and keeps its quote, so a reviewer checks it in seconds.',
		trace: [
			{
				label: 'R-0487',
				mono: true,
				body: `{
  "text": "The lighting and signalling devices shall continue to operate correctly and to remain visible.",
  "source": {
    "regulation": "UN R42",
    "version": "0.2.0",
    "page": 3,
    "paragraph": "6.1.1"
  }
}`,
			},
		],
	},
];

// Stages grouped under a bracket, by step index.
const phases = [
	{ name: 'Read the inputs', from: 1, to: 2 },
	{ name: 'Choose regulations', from: 3, to: 3 },
	{ name: 'Find the paragraphs', from: 4, to: 6 },
	{ name: 'Write and check', from: 7, to: 10 },
];
// From Obligation drafts on, 6.1.1 travels as two rows.
const SPLIT = 7;

const last = steps.length - 1;
const still = matchMedia('(prefers-reduced-motion: reduce)').matches;
const PACE = 2600;

let step = $state(still ? last : 0);
let playing = $state(false);
let started = false;
const cur = $derived(steps[step]);

const go = (i: number) => (step = Math.max(0, Math.min(last, i)));
function pick(i: number) {
	playing = false;
	go(i);
}
function toggle() {
	if (!playing && step === last) step = 0;
	playing = !playing;
}
function key(e: KeyboardEvent) {
	if (e.key === 'ArrowRight') pick(step + 1);
	else if (e.key === 'ArrowLeft') pick(step - 1);
	else return;
	e.preventDefault();
}

$effect(() => {
	if (!playing) return;
	const t = setInterval(() => {
		if (step >= last) playing = false;
		else step += 1;
	}, PACE);
	return () => clearInterval(t);
});

// Plays through once, the first time the diagram is mostly on screen.
function autoplay(node: HTMLElement) {
	if (still) return;
	const io = new IntersectionObserver(
		([e]) => {
			if (!e.isIntersecting || started) return;
			started = true;
			playing = true;
			io.disconnect();
		},
		{ threshold: 0.5 },
	);
	io.observe(node);
	return { destroy: () => io.disconnect() };
}

const pad = (n: number) => String(n).padStart(2, '0');
</script>

<!-- Arrow keys step through the stages once any control inside has focus. -->
<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
<figure
	class="engine"
	aria-label="Engine diagram, arrow keys step through the stages"
	onkeydown={key}
	use:autoplay
>
	<div class="flex flex-wrap items-center gap-2">
		<button type="button" class="ui-btn ui-btn-primary w-20 justify-center" onclick={toggle}>
			{playing ? 'Pause' : step === last ? 'Replay' : 'Play'}
		</button>
		<button type="button" class="ui-btn" onclick={() => pick(step - 1)} disabled={step === 0}>
			Previous
		</button>
		<button type="button" class="ui-btn" onclick={() => pick(step + 1)} disabled={step === last}>
			Next
		</button>
		<span class="ui-label ml-3 tabular-nums">{pad(step + 1)} / {pad(steps.length)}</span>
		<span class="ui-label ml-auto hidden sm:block">Front bumper run</span>
	</div>

	<div class="mt-6 overflow-x-auto pb-2">
		<div class="flex min-w-[1120px]" aria-hidden="true">
			<div class="w-16 shrink-0"></div>
			<div class="flow grid flex-1" style="--n: {steps.length}">
				{#each phases as ph}
					<span
						class="phase {step > ph.to ? 'done' : step >= ph.from ? 'on' : 'ahead'}"
						style="grid-column: {ph.from + 1} / span {ph.to - ph.from + 1}"
					>
						{ph.name}
					</span>
				{/each}
			</div>
		</div>
		<div class="mt-2 flex min-w-[1120px]">
			<div class="lanes relative w-16 shrink-0" aria-hidden="true">
				<span class="ui-label absolute top-[28px]">Model</span>
				<span class="ui-label absolute top-[124px]">Code</span>
				<span class="ui-label absolute top-[164px]">Citation</span>
			</div>
			<div class="flow relative grid flex-1" style="--n: {steps.length}">
				<span class="rail top-[36px]" aria-hidden="true"></span>
				<span class="rail top-[132px]" aria-hidden="true"></span>
				<!-- The citation runs from the parser to the output on its own line: no model touches it. -->
				<span class="cite" aria-hidden="true">
					<span
						class="cite-lit"
						style="width: {(Math.max(0, step - 1) / (last - 1)) * 100}%"
					></span>
				</span>
				{#if step >= 1}
					<span
						class="cite-head ui-label"
						style="left: calc((100% / var(--n)) * {step + 0.5}); transform: translateX({step ===
						last
							? 'calc(-100% + 3rem)'
							: '-50%'})"
						aria-hidden="true"
					>
						UN R42, page 3, 6.1.1
					</span>
				{/if}
				<span
					class="packet {step >= SPLIT ? 'split' : ''}"
					style="left: calc((100% / var(--n)) * {step + 0.5} - 7px)"
					aria-hidden="true"
				></span>
				<span
					class="packet twin {step >= SPLIT ? 'split' : ''}"
					style="left: calc((100% / var(--n)) * {step + 0.5} - 7px)"
					aria-hidden="true"
				></span>
				{#each steps as s, i}
					{@const phase = i < step ? 'done' : i === step ? 'on' : 'ahead'}
					<button
						type="button"
						class="col {phase}"
						aria-label={s.name}
						aria-current={i === step ? 'step' : undefined}
						onclick={() => pick(i)}
					>
						<span class="node-area">
							{#if i > 0}
								<span class="seg seg-l {i <= step ? 'lit' : ''}"></span>
							{/if}
							{#if i < last}
								<span class="seg seg-r {i < step ? 'lit' : ''}"></span>
							{/if}
							{#if i === 0 || i === last}
								<span class="io">
									{#if i === 0}
										spec.md<br>exploded view
									{:else}
										requirements<br>JSON
									{/if}
								</span>
							{/if}
							{#if s.model !== undefined}
								<span class="wire wire-m"></span>
								{#if s.model}
									<span class="tag top-[6px]">{s.model}</span>
								{/if}
								<span class="mark top-[30px]"></span>
							{/if}
							{#if s.code !== undefined}
								<span class="wire wire-c"></span>
								<span class="mark top-[126px]"></span>
								{#if s.code}
									<span class="tag top-[146px]">{s.code}</span>
								{/if}
							{/if}
							{#if i === 1}
								<span class="cite-tick top-[138px] h-[34px] {step >= 1 ? 'lit' : ''}"></span>
							{:else if i === last}
								<span class="cite-tick top-[100px] h-[72px] {step === last ? 'lit' : ''}"></span>
							{/if}
						</span>
						<span class="name">{s.name}</span>
						<span class="count">
							{#if s.count}
								<span class="ui-count text-[1.75rem]">{s.count}</span>
								<span class="ui-label mt-1">{s.unit}</span>
							{/if}
						</span>
					</button>
				{/each}
			</div>
		</div>
	</div>

	<div class="detail mt-6 grid gap-6 border-t border-line pt-6 md:grid-cols-12">
		<div class="md:col-span-5">
			<span class="ui-label">{pad(step + 1)}, {cur.who}</span>
			<h3 class="ui-display mt-2 text-[2rem]">{cur.name}</h3>
			<p class="mt-3 max-w-[52ch] leading-relaxed text-muted">{cur.desc}</p>
			<p class="ui-label mt-4 normal-case tracking-normal text-faint">{cur.file}</p>
		</div>
		<div class="ui-panel p-5 md:col-span-7">
			<span class="ui-label">
				{step === 0 ? 'The case' : 'One paragraph: UN R42 6.1.1'}
			</span>
			{#key step}
				<dl class="trace mt-3 space-y-3">
					{#each cur.trace as r}
						<div>
							<dt class="ui-label text-faint">{r.label}</dt>
							<dd class="mt-1 leading-relaxed">
								{#if Array.isArray(r.body)}
									<ol class="list-decimal space-y-1 pl-5">
										{#each r.body as q}
											<li>{q}</li>
										{/each}
									</ol>
								{:else if r.mono}
									<pre
										class="overflow-x-auto font-mono text-[13px] whitespace-pre-wrap"
									>{r.body}</pre>
								{:else}
									{r.body}
								{/if}
							</dd>
						</div>
					{/each}
				</dl>
			{/key}
		</div>
	</div>
</figure>

<style>
.flow {
	grid-template-columns: repeat(var(--n), minmax(0, 1fr));
}
/* Faint rails along each lane, behind the nodes. */
.rail {
	position: absolute;
	left: 0;
	right: 0;
	height: 1px;
	background: var(--color-line);
}
.col {
	position: relative;
	display: flex;
	flex-direction: column;
	align-items: center;
	padding-bottom: 0.75rem;
	cursor: pointer;
	border-radius: var(--radius-panel);
	transition: background-color 200ms;
}
.col:hover,
.col.on {
	background: var(--color-select);
}
.node-area {
	position: relative;
	display: block;
	width: 100%;
	height: 200px;
}
/* Phase brackets above the columns: a label over a rule with end ticks. */
.phase {
	position: relative;
	margin: 0 0.5rem;
	padding-bottom: 0.6rem;
	text-align: center;
	font-family: var(--font-mono);
	font-size: 11.5px;
	font-weight: 500;
	letter-spacing: 0.08em;
	text-transform: uppercase;
	color: var(--color-faint);
	border-bottom: 1px solid var(--color-line-strong);
	transition:
		color 300ms,
		border-color 300ms;
}
.phase::before,
.phase::after {
	content: "";
	position: absolute;
	bottom: -6px;
	width: 1px;
	height: 6px;
	background: var(--color-line-strong);
	transition: background-color 300ms;
}
.phase::before {
	left: 0;
}
.phase::after {
	right: 0;
}
.phase.done {
	color: var(--color-muted);
}
.phase.on {
	color: var(--color-fg);
	border-color: var(--color-accent);
}
.phase.on::before,
.phase.on::after {
	background: var(--color-accent);
}
/* The citation line, from Parse to the output. */
.cite {
	position: absolute;
	top: 172px;
	left: calc(100% / var(--n) * 1.5);
	width: calc(100% / var(--n) * 10);
	height: 0;
	border-top: 1px dashed var(--color-line-strong);
}
.cite-lit {
	position: absolute;
	top: -1px;
	left: 0;
	height: 2px;
	background: var(--color-accent);
	transition: width 700ms cubic-bezier(0.65, 0, 0.35, 1);
}
.cite-tick {
	position: absolute;
	left: calc(50% - 0.5px);
	width: 1px;
	background: var(--color-line-strong);
	transition: background-color 300ms;
}
.cite-tick.lit {
	background: var(--color-accent);
}
.cite-head {
	position: absolute;
	top: 180px;
	z-index: 1;
	white-space: nowrap;
	color: var(--color-accent);
	pointer-events: none;
	transition: left 700ms cubic-bezier(0.65, 0, 0.35, 1);
}
/* The spine: the path a paragraph takes, lit up to the current stage. */
.seg {
	position: absolute;
	top: 83px;
	height: 2px;
	width: 50%;
	background: var(--color-line-strong);
	transition: background-color 300ms;
}
.seg-l {
	left: 0;
}
.seg-r {
	right: 0;
}
.seg.lit {
	background: var(--color-mark);
}
.wire {
	position: absolute;
	left: calc(50% - 0.5px);
	width: 1px;
	background: var(--color-line-strong);
	transition: background-color 300ms;
}
.wire-m {
	top: 42px;
	height: 41px;
}
.wire-c {
	top: 85px;
	height: 41px;
}
.mark {
	position: absolute;
	left: calc(50% - 6px);
	width: 12px;
	height: 12px;
	background: var(--color-line-strong);
	transition:
		background-color 300ms,
		transform 300ms cubic-bezier(0.3, 1.4, 0.5, 1);
}
.tag {
	position: absolute;
	left: 0;
	right: 0;
	text-align: center;
	font-family: var(--font-mono);
	font-size: 11.5px;
	color: var(--color-faint);
	white-space: nowrap;
	transition: color 300ms;
}
.io {
	position: absolute;
	top: 62px;
	left: 10%;
	right: 10%;
	z-index: 3;
	padding: 4px 2px;
	text-align: center;
	font-family: var(--font-mono);
	font-size: 11px;
	line-height: 1.35;
	color: var(--color-muted);
	background: var(--color-panel);
	border: 1px solid var(--color-line-strong);
	border-radius: var(--radius-panel);
	transition:
		border-color 300ms,
		color 300ms;
}
.name {
	margin-top: 0.25rem;
	padding: 0 0.25rem;
	min-height: 2.6em;
	text-align: center;
	font-size: 13.5px;
	font-weight: 600;
	line-height: 1.25;
	color: var(--color-faint);
	transition: color 300ms;
}
.count {
	display: flex;
	flex-direction: column;
	align-items: center;
	min-height: 3.5rem;
	margin-top: 0.5rem;
	opacity: 0;
	transform: translateY(0.4rem);
	transition:
		opacity 400ms,
		transform 400ms cubic-bezier(0.2, 0.7, 0.2, 1);
}
.done .mark,
.done .wire {
	background: var(--color-mark);
}
.on .mark {
	background: var(--color-accent);
	transform: scale(1.35);
}
.on .wire {
	background: var(--color-accent);
}
.done .name,
.on .name {
	color: var(--color-fg);
}
.on .tag,
.done .tag {
	color: var(--color-muted);
}
.on .io,
.done .io {
	border-color: var(--color-accent);
	color: var(--color-fg);
}
.done .count,
.on .count {
	opacity: 1;
	transform: none;
}
/* The paragraph itself, riding the spine. */
.packet {
	position: absolute;
	top: 77px;
	z-index: 2;
	width: 14px;
	height: 14px;
	background: var(--color-accent);
	pointer-events: none;
	transition:
		left 700ms cubic-bezier(0.65, 0, 0.35, 1),
		transform 400ms cubic-bezier(0.3, 1.4, 0.5, 1),
		opacity 300ms;
}
/* At Obligation drafts the paragraph becomes two rows: the square splits in two. */
.packet.twin {
	opacity: 0;
}
.packet.split {
	transform: translateY(-10px);
}
.packet.twin.split {
	opacity: 1;
	transform: translateY(10px);
}
.trace {
	animation: trace-in 350ms cubic-bezier(0.2, 0.7, 0.2, 1);
}
@keyframes trace-in {
	from {
		opacity: 0;
		transform: translateY(0.5rem);
	}
}

@media (prefers-reduced-motion: reduce) {
	.seg,
	.wire,
	.mark,
	.tag,
	.io,
	.name,
	.count,
	.packet,
	.phase,
	.cite-lit,
	.cite-tick,
	.cite-head {
		transition: none;
	}
	.trace {
		animation: none;
	}
}
</style>
