import type { Assessment, RequirementChange, UpdateRun } from '#lib/api/types.ts';
import { paragraphGroup } from '#lib/graph/model.ts';
import { applied } from './run.ts';

export type GroupStatus = 'changed' | 'new' | 'removed' | 'same';

/** The process graph's view of an update run: the assessment before and after it, and per
 * paragraph group of the run's regulation, its status and the changes in it. */
export type GraphUpdate = {
	run: UpdateRun;
	/** Null when the run is already applied: the assessment is then the after state. */
	before: Assessment | null;
	after: Assessment;
	/** Paragraph groups that keep their own node in both states, so the layout holds. */
	pinned: string[];
	status: Map<string, GroupStatus>;
	changes: Map<string, RequirementChange[]>;
};

/** The groups a change touches: its old paragraph's and its new one's. */
function groups(c: RequirementChange) {
	const out = new Set<string>();
	if (c.oldParagraph) out.add(paragraphGroup(c.oldParagraph));
	if (c.source) out.add(paragraphGroup(c.source.paragraph));
	return out;
}

export function graphUpdate(assessment: Assessment, run: UpdateRun): GraphUpdate {
	const before = run.applied ? null : assessment;
	const after = run.applied ? assessment : applied(assessment, run);
	const changes = new Map<string, RequirementChange[]>();
	for (const c of run.changes)
		for (const g of groups(c)) changes.set(g, [...(changes.get(g) ?? []), c]);

	const count = (a: Assessment, group: string) =>
		a.requirements.filter(
			(r) => r.source.regulation === run.regulation && paragraphGroup(r.source.paragraph) === group,
		).length;
	const status = new Map<string, GroupStatus>();
	for (const [group, list] of changes) {
		const n = count(after, group);
		const was = before
			? count(before, group)
			: n -
				list.filter((c) => c.change === 'added').length +
				list.filter((c) => c.change === 'removed').length;
		status.set(group, was === 0 && n > 0 ? 'new' : was > 0 && n === 0 ? 'removed' : 'changed');
	}
	return { run, before, after, pinned: [...changes.keys()], status, changes };
}
