import type {
	Assessment,
	ChangeKind,
	Hunk,
	Requirement,
	RequirementChange,
	Source,
	UpdateRun,
} from '#lib/api/types.ts';

/** The id a change goes by in the impact list: the requirement's, or the new one for added rows. */
export const changeId = (c: RequirementChange) => c.requirementId ?? c.newId ?? '';

export const changeKinds: ChangeKind[] = ['modified', 'removed', 'added'];

export const short = (regulation: string) => regulation.replace(/^UN /, '');

/** The assessment as it would be after the update, as the backend's apply writes it. */
export function applied(assessment: Assessment, run: UpdateRun): Assessment {
	const { regulation, toVersion } = run;
	let requirements = assessment.requirements.map((r) =>
		r.source.regulation === regulation ? { ...r, source: { ...r.source, version: toVersion } } : r,
	);
	for (const c of run.changes) {
		if (c.change === 'removed') requirements = requirements.filter((r) => r.id !== c.requirementId);
		else if (c.change === 'modified')
			requirements = requirements.map((r) =>
				r.id === c.requirementId
					? { ...r, text: c.newText ?? r.text, source: { ...r.source, ...c.source } }
					: r,
			);
		else
			requirements.push({
				id: changeId(c),
				text: c.newText ?? '',
				source: {
					regulation,
					version: toVersion,
					page: c.source?.page ?? 0,
					paragraph: c.source?.paragraph ?? '',
				},
			});
	}
	const count = requirements.filter((r) => r.source.regulation === regulation).length;
	return {
		...assessment,
		requirements,
		regulations: assessment.regulations.map((d) =>
			d.regulation === regulation ? { ...d, version: toVersion, requirementCount: count } : d,
		),
	};
}

/** The words of one side of a hunk: the old version without insertions, or the new without
 * deletions. */
export function side(hunk: Hunk, which: 'old' | 'new') {
	const drop = which === 'old' ? 'ins' : 'del';
	return hunk.rows
		.filter((r) => r.kind !== (which === 'old' ? 'new' : 'deleted'))
		.map((r) =>
			r.segments
				.filter(([k]) => k !== drop)
				.map(([, t]) => t)
				.join(' '),
		)
		.join(' ');
}

/** "§ 5.13.1.1", "Annex 5 4.1", "Preamble". */
export function paragraphName(label: string) {
	if (label === 'preamble') return 'Preamble';
	return /^(Annex|Appendix)/.test(label) ? label : `§ ${label}`;
}

/** A requirement-shaped entry for the PDF drawer, on the hunk's paragraph in the new version
 * (in the old one for a deleted paragraph), with the other version for the before and after
 * toggle. */
export type Reading = Requirement & { before?: { source: Source; text: string } };

export function hunkReading(run: UpdateRun, hunk: Hunk): Reading {
	const deleted = hunk.status === 'deleted';
	const at = (version: string, page: number, paragraph: string): Source => ({
		regulation: run.regulation,
		version,
		page,
		paragraph,
	});
	return {
		id: paragraphName(hunk.label),
		text: side(hunk, deleted ? 'old' : 'new'),
		source: at(deleted ? run.fromVersion : run.toVersion, hunk.page, hunk.label),
		before:
			hunk.oldLabel && hunk.oldPage && !deleted
				? { source: at(run.fromVersion, hunk.oldPage, hunk.oldLabel), text: side(hunk, 'old') }
				: undefined,
	};
}

/** A change on its new paragraph, for the PDF drawer. Removed rows have no new paragraph. */
export function changeReading(run: UpdateRun, c: RequirementChange): Reading | null {
	if (!c.source) return null;
	const hunk = run.hunks.find((h) => h.id === c.hunk);
	return {
		id: changeId(c),
		text: c.newText ?? '',
		source: { regulation: run.regulation, version: run.toVersion, ...c.source },
		before:
			hunk?.oldLabel && hunk.oldPage
				? {
						source: {
							regulation: run.regulation,
							version: run.fromVersion,
							page: hunk.oldPage,
							paragraph: c.oldParagraph ?? hunk.oldLabel,
						},
						text: c.oldText ?? side(hunk, 'old'),
					}
				: undefined,
	};
}
