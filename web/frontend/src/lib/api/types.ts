export type Source = { regulation: string; version: string; page: number; paragraph: string };

export type Requirement = {
	id: string;
	text: string;
	source: Source;
	testCase?: string;
	rationale?: string;
	/** The regulation's own wording, from the PDF. */
	quote?: string;
	/** The brain's probability that its paragraph is cited. */
	confidence?: number;
};

export type Profile = {
	productType: string;
	vehicleCategory: string;
	parts: string[];
	functions: string[];
	materials: string[];
};

/** One regulation the pipeline considered, whether it made the cut or not. */
export type RegulationDecision = {
	regulation: string;
	version: string;
	title: string;
	included: boolean;
	reason: string;
	requirementCount: number;
};

export type AssessmentStatus = 'running' | 'complete' | 'failed';

export type Assessment = {
	id: string;
	createdAt: string;
	caseName?: string;
	spec: string;
	imageUrl?: string;
	profile: Profile;
	regulations: RegulationDecision[];
	requirements: Requirement[];
	status: AssessmentStatus;
	/** What the pipeline run spent on model calls; empty `models` for a run without a model. */
	cost?: RunCost;
};

export type ModelCost = {
	model: string;
	calls: number;
	input: number;
	output: number;
	cacheWrite: number;
	cacheRead: number;
	costUsd: number;
};

export type RunCost = { totalUsd: number; models: ModelCost[] };

export type PipelineStep =
	| 'profile'
	| 'selection'
	| 'paragraphs'
	| 'requirements'
	| 'done'
	| 'failed';

export type PipelineEvent = {
	step: PipelineStep;
	message: string;
	/** 0..1 over the whole run. */
	progress: number;
	/** Set on the `done` event. */
	assessmentId?: string;
	partial?: {
		profile?: Profile;
		regulations?: RegulationDecision[];
		paragraphCount?: number;
		requirements?: Requirement[];
	};
};

export type ChangeKind = 'modified' | 'removed' | 'added';

export type RequirementChange = {
	requirementId: string | null;
	change: ChangeKind;
	/** The old requirement, on modified and removed rows. */
	oldText?: string;
	newText?: string;
	reason: string;
	/** The paragraph in the new version; removed rows have none. */
	source?: { page: number; paragraph: string };
	/** The id an added requirement gets when the update is applied. */
	newId?: string;
	/** The paragraph the old requirement cites, on modified and removed rows. */
	oldParagraph?: string;
	/** The id of the paragraph hunk this change comes from. */
	hunk?: string;
};

export type HunkStatus = 'amended' | 'moved and amended' | 'new' | 'deleted';

/** A run of words in a diff: unchanged, deleted from the old version, or inserted in the new. */
export type Segment = ['same' | 'del' | 'ins', string];

/** One sentence or list item of a changed paragraph. */
export type HunkRow = { kind: 'unchanged' | 'amended' | 'new' | 'deleted'; segments: Segment[] };

/** One changed paragraph of a regulation, as a word diff of its sentences. */
export type Hunk = {
	id: string;
	/** The label in the new version (in the old one for a deleted paragraph). */
	label: string;
	oldLabel?: string;
	/** The page in the new version (the old one for a deleted paragraph). */
	page: number;
	oldPage?: number;
	status: HunkStatus;
	heading: string;
	rows: HunkRow[];
	addedWords: number;
	removedWords: number;
	/** Requirements that cite this paragraph or one of its ancestors. */
	citedBy: string[];
	/** Ids of the requirement changes it causes (the new id for added rows). */
	changes: string[];
};

export type RunStats = {
	oldParagraphs: number;
	newParagraphs: number;
	oldUnits: number;
	newUnits: number;
	/** Share of the old version's sentences found unchanged in the new one. */
	unchangedShare: number;
	amended: number;
	new: number;
	deleted: number;
	renumbered: number;
	requirements: number;
	citedParagraphs: number;
	changedCitedParagraphs: number;
	seconds: { parse: number; align: number; map: number };
};

/** One comparison of a cited regulation with a newer version, for one assessment. */
export type UpdateRun = {
	id: string;
	assessmentId: string;
	regulation: string;
	title: string;
	fromVersion: string;
	toVersion: string;
	createdAt: string;
	identifiedBy: 'sha256' | 'first page' | 'corpus';
	fileName: string;
	stats: RunStats;
	hunks: Hunk[];
	changes: RequirementChange[];
	applied: boolean;
};

/** A regulation the assessment cites, with the newest version in the corpus. */
export type CitedRegulation = {
	regulation: string;
	title: string;
	version: string;
	/** Set when the corpus holds a newer version than the cited one. */
	latest?: string;
	requirementCount: number;
	/** A stored run comparing the cited version with `latest`. */
	run?: string;
	/** The run applied to reach the cited version. */
	appliedRun?: string;
};

/** Either an uploaded PDF or a cited regulation to compare with its newest version. */
export type UpdateRequest = { file: File } | { regulation: string };

/** Why an upload was not compared; `code` is 'version_needed' when a version must be entered. */
export class UpdateRefusal extends Error {
	constructor(
		message: string,
		readonly code: string,
		readonly regulation?: string,
		readonly version?: string,
	) {
		super(message);
	}
}

export type BriefSentence = { text: string; cites: string[] };

export type BriefSection = { title: string; sentences: BriefSentence[] };

/** Prose summary for developers; every sentence cites requirement ids. */
export type Brief = { sections: BriefSection[] };

/** A spoken answer to a question about part of a report, with what it cost. */
export type AskAnswer = {
	sentences: BriefSentence[];
	costUsd: number;
	spentUsd: number;
	budgetUsd: number;
	/** Set when the server voices answers with ElevenLabs: `GET /api/speak/{speechId}`. */
	speechId?: string;
};

/** A selection to read aloud: the report's own text in it, and its ElevenLabs voice if any. */
export type ReadAloud = {
	text: string;
	speechId?: string;
};

/** Download format expected by the challenge grader. */
export type Submission = {
	team_id: string;
	case_id: string;
	requirements: { id: string; text: string; source: Source }[];
};

export interface ApiClient {
	runAssessment(
		spec: string,
		image: File | Blob | null,
		onEvent: (event: PipelineEvent) => void,
		caseName?: string,
	): Promise<Assessment>;
	listAssessments(): Promise<Assessment[]>;
	getAssessment(id: string): Promise<Assessment | null>;
	listUpdates(id: string): Promise<CitedRegulation[]>;
	/** Rejects with an UpdateRefusal when the file is not compared. */
	createUpdate(id: string, request: UpdateRequest, toVersion?: string): Promise<UpdateRun>;
	getUpdate(id: string, run: string): Promise<UpdateRun | null>;
	applyUpdate(id: string, run: string): Promise<Assessment>;
	undoUpdate(id: string, run: string): Promise<Assessment>;
	/** With `write` false, resolves to null unless a brief was already written. */
	getBrief(requirements: Requirement[], write: boolean): Promise<Brief | null>;
	ask(question: string, selection: string, requirements: Requirement[]): Promise<AskAnswer>;
	read(assessmentId: string, text: string): Promise<ReadAloud>;
}
