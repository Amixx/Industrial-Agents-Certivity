export type Source = { regulation: string; version: string; page: number; paragraph: string };

export type Requirement = {
	id: string;
	text: string;
	source: Source;
	testCase?: string;
	rationale?: string;
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
};

export type PipelineStep = 'profile' | 'selection' | 'paragraphs' | 'requirements' | 'done';

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
	oldText?: string;
	newText?: string;
	reason: string;
	source: { page: number; paragraph: string };
	/** Set on `added` changes: whether the new obligation plausibly applies to the assessed product. */
	relevant?: boolean;
	relevanceNote?: string;
};

export type RegulationUpdate = {
	regulation: string;
	fromVersion: string;
	toVersion: string;
	changes: RequirementChange[];
	/** Paragraph-level counts from the full base-vs-latest diff. */
	stats?: { changed: number; added: number; removed: number };
	applied?: boolean;
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
	checkUpdates(id: string): Promise<RegulationUpdate[]>;
	applyUpdate(id: string, regulation: string): Promise<Assessment>;
}
