import type { RegulationDecision, Requirement } from '#lib/api/types.ts';

/** How a profile facet connects to a regulation. */
export type FacetLink = {
	regulation: string;
	/** Requirements of that regulation whose text mentions the facet. */
	requirementIds: string[];
	/** The selection reason (inclusion or exclusion) mentions the facet. */
	viaReason: boolean;
};

const GENERIC = new Set([
	'and',
	'the',
	'for',
	'with',
	'other',
	'typical',
	'single',
	'multiple',
	'combining',
	'lamp',
	'lamps',
	'light',
	'rear',
	'device',
	'devices',
	'module',
	'modules',
	'part',
	'parts',
	'surface',
	'signalling',
	'presence',
	'visibility',
	'indication',
	'definition',
	'illumination',
	'molded',
	'coating',
	'passenger',
	'car',
]);

/** Links that hold by definition, whatever the texts say. */
const KNOWN: Record<string, string[]> = {
	'rear position lamp': ['UN R48', 'UN R148'],
	'stop lamp': ['UN R48', 'UN R148'],
	'reversing lamp': ['UN R48', 'UN R148'],
	'retro-reflector': ['UN R48', 'UN R150'],
	'light source': ['UN R10'],
};

/** Wording the regulations use for a facet that its own label does not contain. */
const EXTRA: Record<string, RegExp[]> = {
	'light source': [/\bESA\b/, /\belectronic sub-assembl/i],
};

const escapeRegExp = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

function stem(word: string) {
	const s = word.replace(/(ions|ion|ing|ed|ors|or|ers|er|s)$/, '');
	return s.length >= 4 ? s : word;
}

/** Search patterns for a facet label: the short name as a phrase, bracketed phrases, acronyms, distinctive word stems. */
export function facetPatterns(label: string): RegExp[] {
	const name = label.split(/\s+[—-]\s+|\.\s/)[0];
	const patterns: RegExp[] = [];
	const phrases = [name.split(':')[0], ...[...name.matchAll(/\(([^)]+)\)/g)].map((m) => m[1])];
	for (const p of phrases) {
		const clean = p.trim().toLowerCase();
		if (clean.includes(' ') && clean.split(/\s+/).length <= 3)
			patterns.push(new RegExp(`\\b${escapeRegExp(clean)}`, 'i'));
	}
	for (const acronym of name.match(/\b[A-Z][A-Z0-9]{1,4}\b/g) ?? [])
		patterns.push(new RegExp(`\\b${escapeRegExp(acronym)}\\b`));
	for (const word of name.toLowerCase().match(/[a-z]{4,}/g) ?? []) {
		if (GENERIC.has(word)) continue;
		patterns.push(new RegExp(`\\b${escapeRegExp(stem(word))}`, 'i'));
	}
	if (/colou?r/i.test(name)) patterns.push(/\bcolou?r/i);
	patterns.push(...(EXTRA[name.split(':')[0].trim().toLowerCase()] ?? []));
	return patterns;
}

/**
 * Derives facet -> regulation links from text: a requirement counts towards a link when its text
 * matches one of the facet's patterns, and a regulation whose selection reason matches is linked
 * even without matching requirements. A real mapping from the pipeline can replace this function.
 */
export function linkFacet(
	label: string,
	regulations: RegulationDecision[],
	requirements: Requirement[],
): FacetLink[] {
	const patterns = facetPatterns(label);
	const hits = (text: string) => patterns.some((p) => p.test(text));
	const known = KNOWN[label.split(':')[0].trim().toLowerCase()] ?? [];
	const links: FacetLink[] = [];
	for (const reg of regulations) {
		const requirementIds = requirements
			.filter((r) => r.source.regulation === reg.regulation && hits(r.text))
			.map((r) => r.id);
		const viaReason = hits(reg.reason) || known.includes(reg.regulation);
		if (requirementIds.length || viaReason)
			links.push({ regulation: reg.regulation, requirementIds, viaReason });
	}
	return links;
}
