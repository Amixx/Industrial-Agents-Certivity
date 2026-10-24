import index from './fixtures/regulations.json';
import type { Source } from './types.ts';

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
