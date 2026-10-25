import type { Requirement } from '#lib/api/types.ts';

/** Short citation label, e.g. "R148 5.2.7". */
export function citeLabel(req: Requirement): string {
	return `${req.source.regulation.replace(/^UN /, '')} ${req.source.paragraph}`;
}
