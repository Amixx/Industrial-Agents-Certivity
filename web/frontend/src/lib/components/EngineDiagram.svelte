<script lang="ts">
// The engine's data flow, one step at a time: the stages of brain/pipeline.py on a model lane
// and a code lane, with a real paragraph traced through each. Every loop traces the next of
// seven paragraphs from the front bumper run, one per selected regulation; counts, scores and rows come from
// out/heldout-api.json and its log, paragraph texts from the parsed corpus.
import StepControls from './StepControls.svelte';
import StepDetail from './StepDetail.svelte';
import { type Detail, type Row, Stepper } from './stepper.svelte.ts';

type Example = {
	reg: string;
	title: string;
	prob: string;
	version: string;
	page: number;
	label: string;
	text: string;
	parent: { label: string; text: string };
	// What the paragraph or its parent points to, from the reference graph.
	cites?: string;
	score: string;
	numbers: string;
	rows: { id: string; text: string }[];
};

const SELECTED = ['UN R10', 'UN R26', 'UN R42', 'UN R48', 'UN R127', 'UN R148', 'UN GTR 9'];

// Ordered so consecutive rounds switch regulation and topic: impact, lighting, EMC.
const examples: Example[] = [
	{
		reg: 'UN R26',
		title: 'External projections of passenger cars',
		prob: '0.85',
		version: '4.0.0',
		page: 6,
		label: '6.5.2',
		text: 'If the line of the bumper which corresponds to the outline contour of the car vertical projection is on a rigid surface, that surface shall have a minimum radius of curvature of 5 mm at all its points lying from the contour line to 20 mm inward, and a minimum radius of curvature of 2.5 mm in all other cases. This provision applies to that part of the zone lying from the contour line to 20 mm inward which is situated between and in front (or rear in case of the rear bumper) of tangential points with the contour line of two vertical planes each forming with the longitudinal plane of symmetry of the vehicle an angle of 15° (see Fig. 1).',
		parent: { label: '6.5', text: 'Bumpers' },
		score: '0.84',
		numbers: '5 mm, 20 mm and 2.5 mm, all in the source paragraph',
		rows: [
			{
				id: 'R-0111',
				text: 'If the line of the bumper which corresponds to the outline contour of the car vertical projection is on a rigid surface, that surface shall have a minimum radius of curvature of 5 mm at all its points lying from the contour line to 20 mm inward',
			},
			{ id: 'R-0112', text: 'and a minimum radius of curvature of 2.5 mm in all other cases.' },
		],
	},
	{
		reg: 'UN R48',
		title: 'Installation of lighting and light-signalling devices',
		prob: '0.85',
		version: '9.3.0',
		page: 42,
		label: '6.5.4.2.2',
		text: 'The height of the direction-indicator lamps of categories 1, 1a, 1b, 2a and 2b, measured in accordance with paragraph 5.8., shall not be less than 350 mm and not more than 1,500 mm.',
		parent: { label: '6.5.4.2', text: 'In height: above the ground.' },
		cites: 'Paragraph 5.8, how lamp heights are measured',
		score: '0.47',
		numbers: '350 mm and 1,500 mm, both in the source paragraph',
		rows: [
			{
				id: 'R-0221',
				text: 'The height of the direction-indicator lamps of categories 1, 1a, 1b, 2a and 2b, measured in accordance with paragraph 5.8., shall not be less than 350 mm and not more than 1,500 mm.',
			},
		],
	},
	{
		reg: 'UN GTR 9',
		title: 'Pedestrian safety',
		prob: '0.50',
		version: '0.3.0',
		page: 85,
		label: '5.1.2',
		text: 'When tested in accordance with paragraph 7.1.2. (upper legform to bumper), the instantaneous sum of the impact forces with respect to time shall not exceed 7.5 kN and the bending moment on the test impactor shall not exceed 510 Nm.',
		parent: { label: '5.1', text: 'Legform to bumper:' },
		cites: 'Paragraph 7.1.2, the upper legform to bumper test',
		score: '0.79',
		numbers: '7.5 kN and 510 Nm, both in the source paragraph',
		rows: [
			{
				id: 'R-0523',
				text: 'When tested in accordance with paragraph 7.1.2. (upper legform to bumper), the instantaneous sum of the impact forces with respect to time shall not exceed 7.5 kN',
			},
			{ id: 'R-0524', text: 'the bending moment on the test impactor shall not exceed 510 Nm.' },
		],
	},
	{
		reg: 'UN R148',
		title: 'Light-Signalling Devices (LSD)',
		prob: '0.85',
		version: '1.6.0',
		page: 19,
		label: '5.4.3',
		text: 'Minimum or maximum area of apparent surface: The area of the apparent surface in the direction of the axis of reference of the daytime running lamp shall be not less than 25 cm2 and not more than 200 cm2. When a daytime running lamp is to be type approved as a lamp marked “D”, the apparent surface of such a lamp shall not be more than 100 cm2.',
		parent: { label: '5.4', text: 'Daytime running lamps (RL)' },
		score: '0.48',
		numbers: '25 cm2, 200 cm2 and 100 cm2, all in the source paragraph',
		rows: [
			{
				id: 'R-0413',
				text: 'The area of the apparent surface in the direction of the axis of reference of the daytime running lamp shall be not less than 25 cm2 and not more than 200 cm2.',
			},
			{
				id: 'R-0414',
				text: 'When a daytime running lamp is to be type approved as a lamp marked “D”, the apparent surface of such a lamp shall not be more than 100 cm2.',
			},
		],
	},
	{
		reg: 'UN R42',
		title: 'Front and rear protective devices',
		prob: '0.75',
		version: '0.2.0',
		page: 3,
		label: '6.1.1',
		text: 'The lighting and signalling devices shall continue to operate correctly and to remain visible. Should the adjustment of the factory-fitted lighting devices be disturbed, it may be corrected to conform to the required specifications, provided this can be done by the normal means of adjustment. Bulbs may be replaced in the event of filament failure.',
		parent: {
			label: '6.1',
			text: 'After each impact test made in accordance with the conditions and procedure specified in annex 3 to this Regulation, the vehicle shall meet the following requirements:',
		},
		cites: 'Annex 3, through its parent: the impact test conditions and procedure',
		score: '0.55',
		numbers: 'None to check',
		rows: [
			{
				id: 'R-0487',
				text: 'The lighting and signalling devices shall continue to operate correctly and to remain visible.',
			},
			{
				id: 'R-0488',
				text: 'Should the adjustment of the factory-fitted lighting devices be disturbed, it may be corrected to conform to the required specifications, provided this can be done by the normal means of adjustment.',
			},
		],
	},
	{
		reg: 'UN R10',
		title: 'Electromagnetic compatibility',
		prob: '0.95',
		version: '7.2.0',
		page: 12,
		label: '6.8.2.2',
		text: 'The ESA representative of its type shall be considered as complying with immunity requirements if, during the tests performed in accordance with Annex 9, there shall be no degradation of performance of "immunity related functions".',
		parent: { label: '6.8.2', text: 'ESA immunity type approval limits' },
		cites: 'Annex 9, the immunity test methods',
		score: '0.63',
		numbers: 'None to check',
		rows: [
			{
				id: 'R-0029',
				text: 'The ESA representative of its type shall be considered as complying with immunity requirements if, during the tests performed in accordance with Annex 9, there shall be no degradation of performance of "immunity related functions".',
			},
		],
	},
	{
		reg: 'UN R127',
		title: 'Pedestrian safety',
		prob: '0.85',
		version: '4.3.0',
		page: 36,
		label: 'Annex 5 2.7',
		text: 'The impact velocity of the upper legform impactor when striking the bumper shall be 11.1 m/s ± 0.2 m/s.',
		parent: { label: 'Annex 5 2', text: 'Upper legform to bumper' },
		score: '0.41',
		numbers: '11.1 m/s and 0.2 m/s, both in the source paragraph',
		rows: [
			{
				id: 'R-0486',
				text: 'The impact velocity of the upper legform impactor when striking the bumper shall be 11.1 m/s ± 0.2 m/s.',
			},
		],
	},
];

type Step = Omit<Detail, 'trace'> & {
	trace: (e: Example) => Row[];
	// Node on each lane, with a tag when someone other than the usual worker does it;
	// undefined means the lane is not used.
	model?: string;
	code?: string;
	count?: string;
	unit?: string;
};

// Real candidate paragraphs of the seven regulations, flicked through while Jev scores all 3,240.
const CANDIDATES = [
	'UN R42, page 7, Annex 3 2.3',
	'UN R26, page 2, 2.7.4',
	'UN R48, page 91, Annex 1 9.32',
	'UN R10, page 22, 7.15',
	'UN R127, page 7, 2.18',
	'UN GTR 9, page 76, 3.36',
	'UN R148, page 25, 5.10.6',
	'UN R48, page 118, Annex 12 2.1',
	'UN R10, page 10, 6.7',
	'UN R26, page 4, 5',
	'UN R148, page 42, Annex 4 1.2.1',
	'UN R42, page 7, Annex 3 2.3.6',
	'UN R127, page 44, Annex 6 2.4.1',
	'UN GTR 9, page 74, 3.24',
	'UN R127, page 24, Annex 1 11',
	'UN GTR 9, page 114, 8.3.2',
	'UN R48, page 25, 5.21',
	'UN R10, page 96, Annex 8 3.2',
	'UN R148, page 9, 3.3.5.1.1',
	'UN R42, page 7, Annex 3 2.2.5',
	'UN R26, page 5, 6.4.2',
	'UN R127, page 12, 2.43',
	'UN R148, page 30, Annex 1 9.1.5',
	'UN R26, page 14, Annex 3 1.2',
	'UN R10, page 7, 3.2.10',
	'UN R42, page 7, Annex 3 2.2.4',
	'UN R48, page 7, 2.7.5.3',
	'UN GTR 9, page 92, 6.3.1.2.2',
];

const both = (e: Example, two: string, one: string) => (e.rows.length > 1 ? two : one);

const steps: Step[] = [
	{
		name: 'Spec and exploded view',
		who: 'Input',
		file: 'cases/heldout-front-bumper/spec.md',
		desc: 'A product specification in Markdown and, when there is one, the exploded-view image.',
		trace: () => [
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
		trace: (e) => [
			{ label: `${e.reg}, page ${e.page}`, body: `${e.label} ${e.text}` },
			{ label: 'Record', body: `${e.reg} | ${e.version} | ${e.label}, page ${e.page}`, mono: true },
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
		trace: () => [
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
		trace: (e) => [
			{ label: e.reg, body: e.title },
			{ label: 'Verdict', body: `Kept, probability ${e.prob}` },
			{ label: 'Also kept', body: SELECTED.filter((r) => r !== e.reg).join(', ') },
		],
	},
	{
		name: 'Reference graph',
		who: 'Code',
		file: 'brain/graph.py',
		desc: 'Regular expressions link each paragraph to its parent, to the paragraphs and annexes it cites, and to the definitions it uses. Later stages read a paragraph together with this context.',
		code: '',
		trace: (e) => [
			{ label: `Parent, ${e.parent.label}`, body: e.parent.text },
			...(e.cites ? [{ label: 'Cites', body: e.cites }] : []),
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
		trace: () => [
			{ label: 'Scored', body: 'All 3,240 candidate paragraphs of the 7 regulations' },
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
		trace: (e) => [
			{ label: 'Blended score', body: e.score },
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
		trace: (e) =>
			e.rows.map((r, i) => ({
				label: e.rows.length > 1 ? `Row ${i + 1} quotes` : 'One row, quoting',
				body: r.text,
			})),
	},
	{
		name: 'Verify',
		who: 'Code',
		file: 'brain/verify.py',
		desc: 'Every number in a draft must appear in its source paragraph or an ancestor, every citation must point at the base version, and duplicates go. Drafts that fail are dropped.',
		code: '',
		count: '810',
		unit: 'drafts',
		trace: (e) => [
			{ label: 'Numbers', body: e.numbers },
			{ label: 'Version', body: `${e.version}, the base version` },
			{ label: 'Result', body: both(e, 'Both rows pass', 'The row passes') },
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
		trace: (e) => [
			{ label: 'Result', body: both(e, 'Both rows kept', 'Kept') },
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
		trace: (e) => [
			{
				label: e.label,
				body: both(e, 'Two separate obligations, so two rows', 'One obligation, one row'),
			},
		],
	},
	{
		name: 'Cited requirements',
		who: 'Output',
		file: 'requirements.json',
		desc: 'One row per obligation. Each cites the regulation, base version, page and paragraph, and keeps its quote, so a reviewer checks it in seconds.',
		trace: (e) => [
			{
				label: e.rows[0].id,
				mono: true,
				body: JSON.stringify(
					{
						text: e.rows[0].text,
						source: { regulation: e.reg, version: e.version, page: e.page, paragraph: e.label },
					},
					null,
					2,
				),
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
// From Obligation drafts on, a paragraph with two obligations travels as two rows.
const SPLIT = 7;

const st = new Stepper(steps.length, { loop: true });
const last = st.last;
const step = $derived(st.step);
const ex = $derived(examples[st.round % examples.length]);
const cur = $derived({ ...steps[st.step], trace: steps[st.step].trace(ex) });
const split = $derived(step >= SPLIT && ex.rows.length > 1);
// During screening the citation flicks through other candidates, then settles on the traced one.
const SCREEN = 5;
let tick = $state(0);
const scanning = $derived(step === SCREEN && !st.still);
$effect(() => {
	if (!scanning) return;
	const t = setInterval(() => tick++, 140);
	return () => clearInterval(t);
});
</script>

<!-- Arrow keys step through the stages once any control inside has focus. -->
<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
<figure
	class="engine"
	aria-label="Engine diagram, arrow keys step through the stages"
	onkeydown={st.key}
	use:st.autoplay
>
	<StepControls
		{st}
		caption="Front bumper run, paragraph {(st.round % examples.length) + 1} of {examples.length}"
	/>

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
						class="cite-head ui-label {scanning ? 'scan' : ''}"
						style="left: calc((100% / var(--n)) * {step + 0.5}); transform: translateX({step ===
						last
							? 'calc(-100% + 3rem)'
							: '-50%'})"
						aria-hidden="true"
					>
						{scanning
							? CANDIDATES[tick % CANDIDATES.length]
							: `${ex.reg}, page ${ex.page}, ${ex.label}`}
					</span>
				{/if}
				<span
					class="packet {split ? 'split' : ''}"
					style="left: calc((100% / var(--n)) * {step + 0.5} - 7px)"
					aria-hidden="true"
				></span>
				<span
					class="packet twin {split ? 'split' : ''}"
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
						onclick={() => st.pick(i)}
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

	<StepDetail
		{step}
		{cur}
		title={step === 0 ? 'The case' : `One paragraph: ${ex.reg} ${ex.label}`}
	/>
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
.cite-head.scan {
	color: var(--color-faint);
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
}
</style>
