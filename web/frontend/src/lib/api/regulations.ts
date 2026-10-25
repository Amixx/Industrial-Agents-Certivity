import index from './fixtures/regulations.json';
import type { Assessment, Source } from './types.ts';

type IndexEntry = {
	regulation: string;
	title: string;
	versions: { role: string; version_label: string; files: { name: string }[] }[];
};

export const regulationIndex: IndexEntry[] = index;

export function regulationTitle(regulation: string) {
	return regulationIndex.find((r) => r.regulation === regulation)?.title ?? '';
}

export function pdfUrl({ regulation, version }: Pick<Source, 'regulation' | 'version'>) {
	const entry = regulationIndex.find((r) => r.regulation === regulation);
	const v = entry?.versions.find((v) => v.version_label === version);
	if (!v) return null;
	return `/pdfs/${regulation.replace(' ', '_')}/${v.role}/${v.files[0].name}`;
}

const versionKey = (v: string) => v.split('.').map(Number);

function newer(a: string, b: string) {
	const [x, y] = [versionKey(a), versionKey(b)];
	for (let i = 0; i < Math.max(x.length, y.length); i++)
		if ((x[i] ?? 0) !== (y[i] ?? 0)) return (x[i] ?? 0) > (y[i] ?? 0);
	return false;
}

/** The newest version of a regulation in the corpus, if it is newer than `version`. */
export function newerVersion(regulation: string, version: string) {
	const versions = regulationIndex.find((r) => r.regulation === regulation)?.versions ?? [];
	const newest = versions
		.map((v) => v.version_label)
		.reduce<string | null>((best, v) => (!best || newer(v, best) ? v : best), null);
	return newest && newer(newest, version) ? newest : null;
}

/** The assessment's cited regulations that have a newer version in the corpus. */
export function pendingUpdates(assessment: Assessment) {
	return assessment.regulations.filter((d) => d.included && newerVersion(d.regulation, d.version));
}
