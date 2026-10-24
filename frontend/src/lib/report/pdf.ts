import regulations from '#lib/api/fixtures/regulations.json';
import type { Source } from '#lib/api/types.ts';

type CatalogVersion = { role: string; version_label: string; files: { name: string }[] };
type CatalogRegulation = { regulation: string; versions: CatalogVersion[] };

const catalog = regulations as CatalogRegulation[];

/** Static PDF path for a cited source, or null when the version isn't in the catalog. */
export function pdfHref(source: Source): string | null {
	const reg = catalog.find((r) => r.regulation === source.regulation);
	const version = reg?.versions.find((v) => v.version_label === source.version);
	const file = version?.files[0]?.name;
	if (!version || !file) return null;
	return `/pdfs/${source.regulation.replace(/ /g, '_')}/${version.role}/${file}#page=${source.page}`;
}
