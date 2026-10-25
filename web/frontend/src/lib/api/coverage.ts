import type { RegulationDecision, Source } from './types.ts';

export type MissReason = 'below_cut' | 'split_finer' | 'worded_differently';
export type CutStage = 'paragraph' | 'section' | 'confidence';

export type CoverageRow = { id: string; text: string; source: Source };

/** An expert requirement the local judge left unmatched, with the one reason it gives. */
export type Miss = CoverageRow & {
	reason: MissReason;
	/** For `below_cut`, when the run kept them: the paragraph's score and the cut it fell under. */
	score?: number;
	cut?: number;
	stage?: CutStage;
	/** sudo's most similar requirement on the same paragraph, by the judge's similarity. */
	nearest?: CoverageRow & {
		similarity: number;
		/** The expert requirement the judge paired this row with instead, if any. */
		pairedWith?: string;
	};
};

/** A sudo requirement the local judge paired with no expert requirement. */
export type Extra = CoverageRow & { onExpertParagraph: boolean };

export type LocalScore = {
	expected: number;
	submitted: number;
	matched: number;
	precision: number;
	recall: number;
	f2: number;
};

export type PlatformUpload = {
	/** As the run log writes it, with its time zone where it gives one. */
	at: string;
	f2: number;
	/** Expert rows matched; absent on the held-out case, whose expert answer is hidden. */
	matched?: number;
	precision?: number;
	recall?: number;
};

export type PlatformScore = { file: string; rows: number; uploads: PlatformUpload[] };

export type NearCut = {
	source: Source;
	/** The start of the paragraph. */
	text?: string;
	score: number;
	cut?: number;
	stage?: CutStage;
	kept: boolean;
};

export type Coverage = {
	/** The case folder whose spec the assessment ran on. */
	case?: string;
	hasAnswer: boolean;
	local?: LocalScore;
	platform?: PlatformScore;
	missed: Miss[];
	extra: Extra[];
	excluded: RegulationDecision[];
	nearCut: NearCut[];
	/** Expert rows the assessment holds word for word; all of them means it measures nothing. */
	expertCopies: number;
	/** A stored engine run on the same case, to compare instead. */
	engineRun?: string;
};

export async function getCoverage(id: string): Promise<Coverage> {
	const res = await fetch(`/api/assessments/${id}/coverage`);
	if (!res.ok) {
		const body = await res.json().catch(() => null);
		throw new Error(body?.detail ?? `${res.status} ${res.statusText}`);
	}
	return res.json();
}
