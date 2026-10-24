import type { Assessment, RegulationDecision, Requirement } from '#lib/api/types.ts';
import { type FacetLink, linkFacet } from './mapping.ts';

export type FacetGroup = 'product' | 'parts' | 'functions' | 'materials';

export const groupLabels: Record<FacetGroup, string> = {
	product: 'Product',
	parts: 'Parts',
	functions: 'Functions',
	materials: 'Materials',
};

type Box = { id: string; x: number; y: number; w: number; h: number };

export type SpecNode = Box & { kind: 'spec' };
export type FacetNode = Box & {
	kind: 'facet';
	group: FacetGroup;
	label: string;
	detail?: string;
	links: FacetLink[];
};
export type RegulationNode = Box & { kind: 'regulation'; decision: RegulationDecision };
export type ClusterNode = Box & {
	kind: 'cluster';
	regulation: string;
	label: string;
	requirements: Requirement[];
};
export type GraphNode = SpecNode | FacetNode | RegulationNode | ClusterNode;

export type EdgeKind = 'spec' | 'facet' | 'reason' | 'cluster';
export type GraphEdge = {
	id: string;
	from: string;
	to: string;
	kind: EdgeKind;
	weight: number;
	width: number;
	path: string;
};

export type GroupHeader = { group: FacetGroup; y: number };

export type Graph = {
	nodes: GraphNode[];
	edges: GraphEdge[];
	headers: GroupHeader[];
	width: number;
	height: number;
	connected: (id: string) => Set<string>;
};

export const columns = {
	spec: { x: 0, w: 130 },
	facet: { x: 170, w: 210 },
	regulation: { x: 520, w: 200 },
	cluster: { x: 800, w: 150 },
};

const FACET_H = 30;
const FACET_GAP = 4;
const GROUP_HEADER = 22;
const GROUP_GAP = 14;
const CLUSTER_H = 24;
const CLUSTER_GAP = 3;
const CLUSTERS_SHOWN = 4;
const BLOCK_GAP = 16;
const REG_MIN_H = 70;
/** Edge width per requirement, on every edge kind. */
const PX_PER_REQUIREMENT = 0.45;

const edgeWidth = (weight: number) => Math.max(1.5, weight * PX_PER_REQUIREMENT);

/** Groups at the second paragraph level ("6.10"), or by annex ("Annex 9"). */
function paragraphGroup(paragraph: string) {
	const annex = paragraph.match(/^Annex \d+/);
	return annex ? annex[0] : paragraph.split('.').slice(0, 2).join('.');
}

const naturalCompare = (a: string, b: string) =>
	a.localeCompare(b, 'en', { numeric: true, sensitivity: 'base' });

function clustersFor(regulation: string, requirements: Requirement[]) {
	const groups = new Map<string, Requirement[]>();
	for (const r of requirements.filter((r) => r.source.regulation === regulation)) {
		const key = paragraphGroup(r.source.paragraph);
		groups.set(key, [...(groups.get(key) ?? []), r]);
	}
	const bySize = [...groups].sort((a, b) => b[1].length - a[1].length);
	const shown = bySize
		.slice(0, CLUSTERS_SHOWN)
		.sort((a, b) => naturalCompare(a[0], b[0]))
		.map(([key, reqs]) => ({ label: key.startsWith('Annex') ? key : `§ ${key}`, reqs }));
	const rest = bySize.slice(CLUSTERS_SHOWN);
	if (rest.length)
		shown.push({
			label: `${rest.length} more groups`,
			reqs: rest.flatMap(([, reqs]) => reqs),
		});
	return shown;
}

function curve(x1: number, y1: number, x2: number, y2: number) {
	const mx = (x1 + x2) / 2;
	return `M${x1},${y1} C${mx},${y1} ${mx},${y2} ${x2},${y2}`;
}

/** Stacks edge ends along a node side, ordered by the far end's height, centred on the node. */
function ports(
	node: Box,
	edges: { id: string; width: number; other: number }[],
): Map<string, number> {
	const sorted = [...edges].sort((a, b) => a.other - b.other);
	const total = sorted.reduce((s, e) => s + e.width, 0);
	const scale = total > node.h - 4 ? (node.h - 4) / total : 1;
	let y = node.y + node.h / 2 - (total * scale) / 2;
	const out = new Map<string, number>();
	for (const e of sorted) {
		out.set(e.id, y + (e.width * scale) / 2);
		y += e.width * scale;
	}
	return out;
}

export function buildGraph(assessment: Assessment): Graph {
	const { profile, requirements } = assessment;
	const regulations = assessment.regulations.filter((r) => r.included);
	const nodes: GraphNode[] = [];
	const headers: GroupHeader[] = [];

	/** [group, label, detail, text the mapping searches for]. */
	const facetSources: [FacetGroup, string, string | undefined, string][] = [
		['product', profile.productType.split(/\s+[—-]\s+/)[0], 'Product type', profile.productType],
		[
			'product',
			profile.vehicleCategory.split(/\s+[—-]\s+/)[0],
			'Vehicle category',
			profile.vehicleCategory,
		],
		...profile.parts.map((p): [FacetGroup, string, undefined, string] => [
			'parts',
			p,
			undefined,
			p,
		]),
		...profile.functions.map((f): [FacetGroup, string, undefined, string] => [
			'functions',
			f,
			undefined,
			f,
		]),
		...profile.materials.map((m): [FacetGroup, string, string, string] => {
			const [part, material] = m.split(/:\s*/);
			return ['materials', part, material, m];
		}),
	];

	let y = 0;
	let group: FacetGroup | null = null;
	facetSources.forEach(([g, label, detail, text], i) => {
		if (g !== group) {
			if (group) y += GROUP_GAP;
			headers.push({ group: g, y });
			y += GROUP_HEADER;
			group = g;
		}
		nodes.push({
			kind: 'facet',
			id: `f${i}`,
			group: g,
			label,
			detail,
			links: linkFacet(text, regulations, requirements),
			...columns.facet,
			y,
			h: FACET_H,
		});
		y += FACET_H + FACET_GAP;
	});
	const facetBottom = y - FACET_GAP;

	y = GROUP_HEADER;
	const clusterNodes: ClusterNode[] = [];
	for (const decision of regulations) {
		const clusters = clustersFor(decision.regulation, requirements);
		const blockH = clusters.length * (CLUSTER_H + CLUSTER_GAP) - CLUSTER_GAP;
		const regH = Math.max(REG_MIN_H, decision.requirementCount * PX_PER_REQUIREMENT + 8);
		const height = Math.max(blockH, regH);
		nodes.push({
			kind: 'regulation',
			id: `r:${decision.regulation}`,
			decision,
			...columns.regulation,
			y: y + (height - regH) / 2,
			h: regH,
		});
		let cy = y + (height - blockH) / 2;
		for (const c of clusters) {
			clusterNodes.push({
				kind: 'cluster',
				id: `c:${decision.regulation}:${c.label}`,
				regulation: decision.regulation,
				label: c.label,
				requirements: c.reqs,
				...columns.cluster,
				y: cy,
				h: CLUSTER_H,
			});
			cy += CLUSTER_H + CLUSTER_GAP;
		}
		y += height + BLOCK_GAP;
	}
	nodes.push(...clusterNodes);

	const regBottom = y - BLOCK_GAP;

	const height = Math.max(facetBottom, regBottom);
	const specH = 180;
	const spec: SpecNode = {
		kind: 'spec',
		id: 'spec',
		...columns.spec,
		y: Math.max(0, facetBottom / 2 - specH / 2),
		h: specH,
	};
	nodes.unshift(spec);

	const byId = new Map(nodes.map((n) => [n.id, n]));
	const center = (id: string) => {
		const n = byId.get(id) as Box;
		return n.y + n.h / 2;
	};
	const raw: Omit<GraphEdge, 'path'>[] = [];
	const facets = nodes.filter((n): n is FacetNode => n.kind === 'facet');
	for (const f of facets) {
		raw.push({ id: `spec-${f.id}`, from: 'spec', to: f.id, kind: 'spec', weight: 0, width: 1 });
		for (const link of f.links) {
			const weight = link.requirementIds.length;
			raw.push({
				id: `${f.id}-${link.regulation}`,
				from: f.id,
				to: `r:${link.regulation}`,
				kind: weight ? 'facet' : 'reason',
				weight,
				width: weight ? edgeWidth(weight) : 1,
			});
		}
	}
	for (const c of clusterNodes)
		raw.push({
			id: `${c.regulation}-${c.id}`,
			from: `r:${c.regulation}`,
			to: c.id,
			kind: 'cluster',
			weight: c.requirements.length,
			width: edgeWidth(c.requirements.length),
		});

	const outPorts = new Map<string, number>();
	const inPorts = new Map<string, number>();
	for (const n of nodes) {
		const out = raw.filter((e) => e.from === n.id);
		const inc = raw.filter((e) => e.to === n.id);
		for (const [k, v] of ports(
			n,
			out.map((e) => ({ id: e.id, width: e.width, other: center(e.to) })),
		))
			outPorts.set(k, v);
		for (const [k, v] of ports(
			n,
			inc.map((e) => ({ id: e.id, width: e.width, other: center(e.from) })),
		))
			inPorts.set(k, v);
	}
	const edges: GraphEdge[] = raw.map((e) => {
		const a = byId.get(e.from) as Box;
		const b = byId.get(e.to) as Box;
		return {
			...e,
			path: curve(a.x + a.w, outPorts.get(e.id) ?? 0, b.x, inPorts.get(e.id) ?? 0),
		};
	});

	const facetsFor = (regulation: string, ids?: Set<string>) =>
		facets.filter((f) =>
			f.links.some(
				(l) => l.regulation === regulation && (!ids || l.requirementIds.some((id) => ids.has(id))),
			),
		);

	function connected(id: string): Set<string> {
		const node = byId.get(id);
		const set = new Set<string>([id, 'spec']);
		if (!node || node.kind === 'spec') return new Set(nodes.map((n) => n.id));
		if (node.kind === 'facet') {
			const ids = new Set(node.links.flatMap((l) => l.requirementIds));
			for (const l of node.links) set.add(`r:${l.regulation}`);
			for (const c of clusterNodes) if (c.requirements.some((r) => ids.has(r.id))) set.add(c.id);
		} else if (node.kind === 'regulation') {
			for (const f of facetsFor(node.decision.regulation)) set.add(f.id);
			for (const c of clusterNodes) if (c.regulation === node.decision.regulation) set.add(c.id);
		} else {
			set.add(`r:${node.regulation}`);
			const ids = new Set(node.requirements.map((r) => r.id));
			for (const f of facetsFor(node.regulation, ids)) set.add(f.id);
		}
		return set;
	}

	return {
		nodes,
		edges,
		headers,
		width: columns.cluster.x + columns.cluster.w,
		height,
		connected,
	};
}
