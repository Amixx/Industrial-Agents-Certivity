// Parametric front bumper for the 3D exploded view. Every part is swept along one plan curve,
// the fascia's line seen from above, so the parts fit together when assembled. Units are
// half metres, Y up, the vehicle's front faces +Z and the parts explode along Z.

import * as THREE from 'three';
import type { ProductModel } from './scene3d.ts';

type V2 = [number, number];

// Half the fascia's plan line, from the centre out to the wheel arch, in (x, z).
const PLAN_HALF: V2[] = [
	[0, 0],
	[0.7, -0.05],
	[1.2, -0.16],
	[1.5, -0.32],
	[1.66, -0.52],
	[1.7, -0.7],
];

const PLAN = new THREE.CatmullRomCurve3(
	[
		...PLAN_HALF.slice(1)
			.reverse()
			.map(([x, z]) => [-x, z]),
		...PLAN_HALF,
	].map(([x, z]) => new THREE.Vector3(x, 0, z)),
	false,
	'centripetal',
);
const LENGTH = PLAN.getLength();
/** Arc length from the centre to either end of the fascia. */
const END = LENGTH / 2;

// Fascia section, top to bottom, as (offset along the plan normal, height): it rolls back
// under the bonnet at the top, pushes forward into a chin and tucks in underneath.
const SECTION = new THREE.SplineCurve(
	(
		[
			[-0.3, 0.5],
			[-0.12, 0.46],
			[-0.045, 0.4],
			[0, 0.2],
			[0.03, 0],
			[0.05, -0.2],
			[0.045, -0.34],
			[0, -0.42],
			[-0.08, -0.46],
		] as V2[]
	).map(([n, y]) => new THREE.Vector2(n, y)),
).getSpacedPoints(400);
const TOP = SECTION[0].y;
const BOTTOM = SECTION[SECTION.length - 1].y;

// Openings in the fascia, as arc length from the centre and height.
const GRILL = { a0: -0.7, a1: 0.7, y0: 0.02, y1: 0.36 };
const INTAKE = { a0: -1.02, a1: 1.02, y0: -0.36, y1: -0.16 };
const SIDE_INTAKES = [
	{ a0: -1.52, a1: -1.18, y0: -0.3, y1: -0.04 },
	{ a0: 1.18, a1: 1.52, y0: -0.3, y1: -0.04 },
];
const OPENINGS = [GRILL, INTAKE, ...SIDE_INTAKES];

/** Fascia surface offset along the plan normal at height y. */
function profile(y: number) {
	const i = SECTION.findIndex((p) => p.y <= y);
	if (i <= 0) return SECTION[Math.max(0, i)].x;
	const a = SECTION[i - 1];
	const b = SECTION[i];
	return a.x + ((b.x - a.x) * (y - a.y)) / (b.y - a.y || 1);
}

/** Point and outward normal of the plan curve, `a` along it from the centre. */
function frame(a: number) {
	const u = Math.min(1, Math.max(0, 0.5 + a / LENGTH));
	const p = PLAN.getPointAt(u);
	const t = PLAN.getTangentAt(u);
	return { p, n: new THREE.Vector3(-t.z, 0, t.x) };
}

/** World position at `a` along the plan, `n` out along its normal, height `y`. */
function at(a: number, n: number, y: number) {
	const f = frame(a);
	return new THREE.Vector3(f.p.x + f.n.x * n, y, f.p.z + f.n.z * n);
}

const signedArea = (points: V2[]) =>
	points.reduce((sum, p, i) => {
		const q = points[(i + 1) % points.length];
		return sum + p[0] * q[1] - q[0] * p[1];
	}, 0) / 2;

/**
 * Sweeps a closed cross-section in (normal offset, height) along the plan from `a0` to `a1`.
 * The section is given as runs, each ending where the next begins; a run is shaded smooth
 * and the corners between runs stay sharp.
 */
function sweep(runs: V2[][], a0: number, a1: number) {
	const steps = Math.max(2, Math.ceil((a1 - a0) / 0.02));
	const frames = Array.from({ length: steps + 1 }, (_, i) => frame(a0 + ((a1 - a0) * i) / steps));
	const outline = runs.flatMap((r) => r.slice(0, -1));
	const ccw = signedArea(outline) > 0;
	const positions: number[] = [];
	const indices: number[] = [];
	const push = (f: (typeof frames)[number], [n, y]: V2) =>
		positions.push(f.p.x + f.n.x * n, y, f.p.z + f.n.z * n);

	for (const run of runs) {
		const base = positions.length / 3;
		const m = run.length;
		for (const f of frames) for (const point of run) push(f, point);
		for (let i = 0; i < steps; i++)
			for (let k = 0; k < m - 1; k++) {
				const v = base + i * m + k;
				const next = v + m;
				if (ccw) indices.push(v, next, v + 1, next, next + 1, v + 1);
				else indices.push(v, v + 1, next, next, v + 1, next + 1);
			}
	}

	const contour = ccw ? outline : [...outline].reverse();
	const triangles = THREE.ShapeUtils.triangulateShape(
		contour.map(([n, y]) => new THREE.Vector2(n, y)),
		[],
	);
	for (const [f, flip] of [
		[frames[0], false],
		[frames[steps], true],
	] as const) {
		const base = positions.length / 3;
		for (const point of contour) push(f, point);
		for (const [i, j, k] of triangles)
			if (flip) indices.push(base + i, base + k, base + j);
			else indices.push(base + i, base + j, base + k);
	}

	const geometry = new THREE.BufferGeometry();
	geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
	geometry.setIndex(indices);
	geometry.computeVertexNormals();
	return geometry;
}

/** A rectangle in (normal offset, height), one run per side so its edges stay sharp. */
function rect(n0: number, n1: number, y0: number, y1: number): V2[][] {
	return [
		[
			[n0, y0],
			[n1, y0],
		],
		[
			[n1, y0],
			[n1, y1],
		],
		[
			[n1, y1],
			[n0, y1],
		],
		[
			[n0, y1],
			[n0, y0],
		],
	];
}

/** The fascia's skin between two heights, `t` thick, offset `lift` out from the fascia. */
function skin(y0: number, y1: number, t: number, lift = 0): V2[][] {
	const count = Math.max(2, Math.ceil((y1 - y0) / 0.01));
	const ys = Array.from({ length: count + 1 }, (_, i) => y1 - ((y1 - y0) * i) / count);
	const outer = ys.map((y): V2 => [profile(y) + lift, y]);
	const inner = outer.map(([n, y]): V2 => {
		const slope = (profile(y + 0.001) - profile(y - 0.001)) / 0.002;
		const len = Math.hypot(1, slope);
		return [n - t / len, y + (t * slope) / len];
	});
	inner.reverse();
	return [outer, [outer[count], inner[0]], inner, [inner[count], outer[0]]];
}

/** A mesh placed at `a` along the plan, `n` out along its normal, height `y`, its +Z facing out. */
function place(mesh: THREE.Object3D, a: number, n: number, y: number) {
	const f = frame(a);
	mesh.position.copy(at(a, n, y));
	mesh.lookAt(mesh.position.clone().add(f.n));
	return mesh;
}

const cylinder = (r: number, depth: number) =>
	new THREE.CylinderGeometry(r, r, depth, 32).rotateX(Math.PI / 2);

function buildParts() {
	const parts = new Map<string, THREE.Group>();
	const add = (id: string, ...objects: THREE.Object3D[]) => {
		const group = new THREE.Group();
		group.userData.partId = id;
		group.add(...objects);
		parts.set(id, group);
	};
	// Each part gets its own materials, so selecting one can ghost the rest.
	const paint = () =>
		new THREE.MeshPhysicalMaterial({
			color: 0x9aa1a8,
			roughness: 0.36,
			metalness: 0.35,
			clearcoat: 1,
			clearcoatRoughness: 0.08,
		});
	const blackGloss = () =>
		new THREE.MeshPhysicalMaterial({
			color: 0x111214,
			roughness: 0.22,
			clearcoat: 0.8,
			clearcoatRoughness: 0.1,
		});
	const plastic = (color = 0x2b2e31, roughness = 0.72) =>
		new THREE.MeshStandardMaterial({ color, roughness });

	// The fascia in bands between the openings' top and bottom edges, each band in pieces
	// between the openings that cross it.
	const fasciaPaint = paint();
	const edges = [...new Set([BOTTOM, TOP, ...OPENINGS.flatMap((o) => [o.y0, o.y1])])].sort(
		(p, q) => p - q,
	);
	const panels = edges.slice(0, -1).flatMap((y0, i) => {
		const y1 = edges[i + 1];
		const cuts = OPENINGS.filter((o) => o.y0 <= y0 && o.y1 >= y1).sort((p, q) => p.a0 - q.a0);
		const spans: V2[] = [];
		let from = -END;
		for (const o of cuts) {
			spans.push([from, o.a0]);
			from = o.a1;
		}
		spans.push([from, END]);
		return spans.map(([a0, a1]) => new THREE.Mesh(sweep(skin(y0, y1, 0.03), a0, a1), fasciaPaint));
	});
	// The towing device cover and the charge flap are separate panels set into the fascia.
	const flapPaint = paint();
	add(
		'fascia',
		...panels,
		new THREE.Mesh(sweep(skin(-0.3, -0.18, 0.012, 0.006), 1.57, 1.75), flapPaint),
		new THREE.Mesh(sweep(skin(0.06, 0.26, 0.012, 0.006), -1.12, -0.86), flapPaint),
	);

	// Slatted insert in the upper opening, its blades angled down.
	const grillBlack = blackGloss();
	const slats = Array.from({ length: 6 }, (_, i) => {
		const y = GRILL.y0 + 0.045 + i * 0.056;
		const blade: V2[] = [
			[-0.06, y + 0.016],
			[-0.06, y - 0.004],
			[0.018, y - 0.016],
			[0.018, y + 0.004],
		];
		return new THREE.Mesh(
			sweep(
				blade.map((p, k) => [p, blade[(k + 1) % 4]]),
				GRILL.a0 + 0.03,
				GRILL.a1 - 0.03,
			),
			grillBlack,
		);
	});
	const mullions = [-0.45, -0.15, 0.15, 0.45].map(
		(a) =>
			new THREE.Mesh(
				sweep(rect(-0.06, 0.012, GRILL.y0, GRILL.y1), a - 0.008, a + 0.008),
				grillBlack,
			),
	);
	const frameBars = [
		sweep(rect(-0.07, 0.03, GRILL.y1 - 0.03, GRILL.y1), GRILL.a0, GRILL.a1),
		sweep(rect(-0.07, 0.03, GRILL.y0, GRILL.y0 + 0.03), GRILL.a0, GRILL.a1),
		sweep(rect(-0.07, 0.03, GRILL.y0, GRILL.y1), GRILL.a0, GRILL.a0 + 0.03),
		sweep(rect(-0.07, 0.03, GRILL.y0, GRILL.y1), GRILL.a1 - 0.03, GRILL.a1),
	].map((g) => new THREE.Mesh(g, grillBlack));
	// Honeycomb inserts in the side intakes.
	const inserts = SIDE_INTAKES.flatMap((o) => {
		const rows = Array.from({ length: 5 }, (_, i) =>
			sweep(rect(-0.04, 0.0, o.y0 + 0.02 + i * 0.05, o.y0 + 0.032 + i * 0.05), o.a0, o.a1),
		);
		const cols = Array.from({ length: 6 }, (_, i) => {
			const a = o.a0 + ((o.a1 - o.a0) * (i + 0.5)) / 6;
			return sweep(rect(-0.04, 0.0, o.y0, o.y1), a - 0.006, a + 0.006);
		});
		return [...rows, ...cols].map((geometry) => new THREE.Mesh(geometry, grillBlack));
	});
	add('grill', ...frameBars, ...slats, ...mullions, ...inserts);

	// Plate holder in front of the bar between the two openings.
	const holderBlack = plastic(0x1c1d1f, 0.85);
	const bosses = [-0.42, -0.14, 0.14, 0.42].map((a) =>
		place(new THREE.Mesh(cylinder(0.018, 0.012), holderBlack), a, 0.071, -0.078),
	);
	add(
		'plate-holder',
		new THREE.Mesh(sweep(rect(0.035, 0.065, -0.155, 0.0), -0.52, 0.52), holderBlack),
		...bosses,
	);

	// A light strip framing the grill opening, in a dark channel.
	const strip = new THREE.MeshStandardMaterial({
		color: 0xdfe7f0,
		roughness: 0.25,
		emissive: 0xd8ebff,
		emissiveIntensity: 0,
	});
	const channel = blackGloss();
	const frameAround = (inner: number, outer: number, n0: number, n1: number) => {
		const a0 = GRILL.a0 - outer;
		const a1 = GRILL.a1 + outer;
		return [
			sweep(rect(n0, n1, GRILL.y1 + inner, GRILL.y1 + outer), a0, a1),
			sweep(rect(n0, n1, GRILL.y0 - outer, GRILL.y0 - inner), a0, a1),
			sweep(rect(n0, n1, GRILL.y0 - inner, GRILL.y1 + inner), a0, a0 + outer - inner),
			sweep(rect(n0, n1, GRILL.y0 - inner, GRILL.y1 + inner), a1 - outer + inner, a1),
		];
	};
	add(
		'decorative-lighting',
		...frameAround(0.004, 0.044, 0.0, 0.05).map((geometry) => new THREE.Mesh(geometry, channel)),
		...frameAround(0.016, 0.032, 0.0, 0.062).map((geometry) => new THREE.Mesh(geometry, strip)),
	);

	// Amber direction indicators at the front corners and side markers on the wraparound.
	const amber = new THREE.MeshPhysicalMaterial({
		color: 0xf08a1c,
		roughness: 0.18,
		clearcoat: 1,
		emissive: 0xff8a10,
		emissiveIntensity: 0,
	});
	const signal = (a0: number, a1: number, y0: number, y1: number) =>
		new THREE.Mesh(sweep(skin(y0, y1, 0.03, 0.012), a0, a1), amber);
	add(
		'side-lighting',
		signal(-1.62, -1.22, 0.24, 0.3),
		signal(1.22, 1.62, 0.24, 0.3),
		signal(-END + 0.06, -END + 0.3, 0.08, 0.15),
		signal(END - 0.3, END - 0.06, 0.08, 0.15),
	);

	// Front camera in the middle of the grill.
	const cameraBody = plastic(0x18191b, 0.5);
	const glass = new THREE.MeshPhysicalMaterial({
		color: 0x0a0d12,
		roughness: 0.05,
		clearcoat: 1,
		metalness: 0.4,
	});
	add(
		'camera',
		place(new THREE.Mesh(new THREE.BoxGeometry(0.11, 0.08, 0.1), cameraBody), 0, -0.02, 0.27),
		place(new THREE.Mesh(cylinder(0.022, 0.03), glass), 0, 0.04, 0.27),
	);

	// Radar behind the lower intake at the centre, and a corner radar behind each side.
	const radome = blackGloss();
	const radarBody = plastic(0x3a3d40, 0.6);
	const radar = (a: number, n: number, y: number) => [
		place(new THREE.Mesh(new THREE.BoxGeometry(0.16, 0.13, 0.03), radome), a, n, y),
		place(new THREE.Mesh(new THREE.BoxGeometry(0.14, 0.11, 0.07), radarBody), a, n - 0.05, y),
	];
	add(
		'radar',
		...radar(0, -0.03, -0.27),
		...radar(-1.62, -0.09, 0.02),
		...radar(1.62, -0.09, 0.02),
	);

	// Parking sensors flush in the fascia, and the outside temperature sensor behind the intake.
	const pdcFace = paint();
	const pdcBody = plastic(0x232527, 0.6);
	const spots: V2[] = [
		[0.88, -0.07],
		[1.45, 0.12],
		[1.85, -0.12],
	];
	const pdc = spots.flatMap(([a, y]) =>
		[-a, a].flatMap((side) => [
			place(new THREE.Mesh(cylinder(0.034, 0.012), pdcFace), side, profile(y) - 0.002, y),
			place(new THREE.Mesh(cylinder(0.03, 0.1), pdcBody), side, profile(y) - 0.06, y),
		]),
	);
	add('pdc', ...pdc, place(new THREE.Mesh(cylinder(0.02, 0.07), pdcBody), 0.8, -0.04, -0.24));

	// Pressure tube across the absorber's face with a sensor at each end.
	const tubePath = new THREE.CatmullRomCurve3(
		Array.from({ length: 31 }, (_, i) => at(-1.45 + (2.9 * i) / 30, -0.07, -0.12)),
	);
	const tubeMaterial = plastic(0xbfc3c7, 0.55);
	const podMaterial = plastic(0x2a2c2f, 0.5);
	add(
		'ped-sensors',
		new THREE.Mesh(new THREE.TubeGeometry(tubePath, 120, 0.014, 12, false), tubeMaterial),
		...[-1.5, 1.5].map((a) =>
			place(new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.08, 0.06), podMaterial), a, -0.1, -0.12),
		),
	);

	// EPP foam block behind the fascia, at bumper height.
	const foam = new THREE.MeshStandardMaterial({ color: 0x26282a, roughness: 0.95 });
	add('absorber', new THREE.Mesh(sweep(rect(-0.4, -0.085, -0.36, 0.02), -1.5, 1.5), foam));

	// Underrun beam under the lower lip, with a downturned front edge.
	const beam: V2[] = [
		[-0.5, -0.51],
		[-0.06, -0.51],
		[-0.06, -0.58],
		[-0.035, -0.58],
		[-0.035, -0.49],
		[-0.5, -0.49],
	];
	add(
		'lower-stiffener',
		new THREE.Mesh(
			sweep(
				beam.map((p, k) => [p, beam[(k + 1) % beam.length]]),
				-1.3,
				1.3,
			),
			plastic(0x3b3e42, 0.6),
		),
	);

	// Side brackets and the top mounting rail, with clips, the harness and the keyless-entry aerial.
	const bracketMaterial = plastic(0x2f3134, 0.7);
	const clips = [-1.3, -0.65, 0, 0.65, 1.3].map((a) =>
		place(new THREE.Mesh(cylinder(0.022, 0.05), bracketMaterial), a, -0.29, 0.43),
	);
	const harnessPath = new THREE.CatmullRomCurve3(
		Array.from({ length: 25 }, (_, i) => {
			const a = -1.7 + (3.4 * i) / 24;
			return at(a, -0.46, -0.05 + 0.03 * Math.sin(i * 1.3));
		}),
	);
	add(
		'brackets',
		new THREE.Mesh(sweep(rect(-0.36, -0.22, 0.38, 0.41), -1.5, 1.5), bracketMaterial),
		new THREE.Mesh(sweep(rect(-0.3, -0.06, 0.05, 0.36), -END + 0.12, -END + 0.3), bracketMaterial),
		new THREE.Mesh(sweep(rect(-0.3, -0.06, 0.05, 0.36), END - 0.3, END - 0.12), bracketMaterial),
		new THREE.Mesh(sweep(rect(-0.2, -0.17, 0.3, 0.33), 0.3, 0.8), plastic(0x141516, 0.4)),
		new THREE.Mesh(
			new THREE.TubeGeometry(harnessPath, 120, 0.012, 8, false),
			plastic(0x161718, 0.8),
		),
		...clips,
	);

	return parts;
}

// Exploded offset per part: trim forward, structure back, sensors lifted clear of the fascia.
const SPREAD: Record<string, THREE.Vector3> = {
	grill: new THREE.Vector3(0, 0.05, 3.0),
	'plate-holder': new THREE.Vector3(0, -0.25, 2.3),
	'decorative-lighting': new THREE.Vector3(0, 0.1, 1.6),
	'side-lighting': new THREE.Vector3(0, 0.55, 0.85),
	camera: new THREE.Vector3(0, 1.15, -0.5),
	radar: new THREE.Vector3(0, 1.15, -1.2),
	pdc: new THREE.Vector3(0, 1.25, -1.9),
	'ped-sensors': new THREE.Vector3(0, 0.05, -1.2),
	absorber: new THREE.Vector3(0, 0, -2.0),
	'lower-stiffener': new THREE.Vector3(0, -0.2, -2.8),
	brackets: new THREE.Vector3(0, 0.15, -3.6),
};

export function bumperModel(): ProductModel {
	return {
		parts: buildParts(),
		spread: SPREAD,
		camera: new THREE.Vector3(-9.6, 4.0, 7.3),
		target: new THREE.Vector3(0, 0.15, -0.4),
		fov: 22,
		minDistance: 3,
		maxDistance: 30,
		glow: { 'decorative-lighting': 1.6, 'side-lighting': 2.2 },
		// The vehicle's centreline at bumper height, from behind the brackets to past the grill.
		axis: [new THREE.Vector3(0, 0, -4.4), new THREE.Vector3(0, 0, 3.8)],
	};
}
