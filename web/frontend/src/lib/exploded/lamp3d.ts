// Parametric rear lamp for the 3D exploded view. Every part is built from one face
// outline, so they fit together when assembled. Units are roughly decimetres, Y up,
// the lens faces +Z and the stack explodes along Z.

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { CSS2DObject, CSS2DRenderer } from 'three/addons/renderers/CSS2DRenderer.js';

type V2 = [number, number];

export interface LampLabel {
	id: string;
	number: string;
	name: string;
}

export interface LampScene {
	setExplode(value: number): void;
	setSelected(id: string | null): void;
	setLit(lit: boolean): void;
	/** Keeps this share of the width, from the left, clear of the model. */
	setInset(fraction: number): void;
	/** Where a part's label sits in the view, in pixels from its top left. */
	screenPoint(id: string): { x: number; y: number } | null;
	resetView(): void;
	dispose(): void;
}

// Face outline, counter-clockwise: wide at the bottom, the outboard edge slanted.
const OUTLINE: V2[] = [
	[-0.52, -0.8],
	[0.48, -0.8],
	[0.42, 0.8],
	[-0.1, 0.8],
];

const RETRO = { x: 0.2, y: -0.5, w: 0.3, h: 0.34 };

// Exploded offset along Z per part, rear to front.
const SPREAD: Record<string, number> = {
	fasteners: -2.15,
	housing: -1.45,
	pcb: -0.8,
	reflector: -0.2,
	gasket: 0.4,
	'retro-reflector': 0.95,
	lens: 1.55,
};

const PCB_HOLES: V2[] = [
	[-0.3, -0.62],
	[0.32, -0.62],
	[0.27, 0.62],
];

const CAMERA_HOME = new THREE.Vector3(-8.2, 2.1, 4.4);
const TARGET_HOME = new THREE.Vector3(0, -0.05, -0.3);

function inset(points: V2[], d: number): V2[] {
	const n = points.length;
	const lines = points.map((p, i) => {
		const q = points[(i + 1) % n];
		const dx = q[0] - p[0];
		const dy = q[1] - p[1];
		const len = Math.hypot(dx, dy);
		const nx = -dy / len;
		const ny = dx / len;
		return { px: p[0] + nx * d, py: p[1] + ny * d, dx, dy };
	});
	return lines.map((l, i) => {
		const m = lines[(i + n - 1) % n];
		const det = m.dx * l.dy - m.dy * l.dx;
		const t = ((l.px - m.px) * l.dy - (l.py - m.py) * l.dx) / det;
		return [m.px + m.dx * t, m.py + m.dy * t];
	});
}

function rounded<T extends THREE.Path>(path: T, points: V2[], r: number): T {
	const n = points.length;
	const toward = (a: V2, b: V2): V2 => {
		const len = Math.hypot(b[0] - a[0], b[1] - a[1]);
		return [a[0] + ((b[0] - a[0]) / len) * r, a[1] + ((b[1] - a[1]) / len) * r];
	};
	points.forEach((cur, i) => {
		const a = toward(cur, points[(i + n - 1) % n]);
		const b = toward(cur, points[(i + 1) % n]);
		if (i === 0) path.moveTo(a[0], a[1]);
		else path.lineTo(a[0], a[1]);
		path.quadraticCurveTo(cur[0], cur[1], b[0], b[1]);
	});
	path.closePath();
	return path;
}

function inside(points: V2[], x: number, y: number) {
	return points.every((p, i) => {
		const q = points[(i + 1) % points.length];
		return (q[0] - p[0]) * (y - p[1]) - (q[1] - p[1]) * (x - p[0]) >= 0;
	});
}

function hole(x: number, y: number, r: number) {
	return new THREE.Path().absarc(x, y, r, 0, Math.PI * 2, true);
}

function extrude(shape: THREE.Shape, depth: number, z: number, bevel = 0) {
	const geometry = new THREE.ExtrudeGeometry(shape, {
		depth,
		curveSegments: 24,
		bevelEnabled: bevel > 0,
		bevelThickness: bevel,
		bevelSize: bevel,
		bevelSegments: 4,
	});
	geometry.translate(0, 0, z);
	return geometry;
}

// Optics: a row of large stop-lamp cups across the middle, small cups elsewhere,
// and nothing behind the retro-reflector.
function cups() {
	const area = inset(OUTLINE, 0.11);
	const out: { x: number; y: number; r: number }[] = [];
	const clearOfRetro = (x: number, y: number, r: number) =>
		Math.abs(x - RETRO.x) > RETRO.w / 2 + r || Math.abs(y - RETRO.y) > RETRO.h / 2 + r;
	for (let y = -0.66; y <= 0.68; y += 0.1) {
		if (y > -0.18 && y < 0.12) continue;
		for (let x = -0.5; x <= 0.5; x += 0.1) {
			if (inside(inset(area, 0.042), x, y) && clearOfRetro(x, y, 0.042))
				out.push({ x, y, r: 0.042 });
		}
	}
	for (let x = -0.08; x <= 0.3; x += 0.165) {
		if (inside(inset(area, 0.07), x, -0.03)) out.push({ x, y: -0.03, r: 0.075 });
	}
	return out;
}

function ribbedNormalMap() {
	const size = 64;
	const data = new Uint8Array(size * 4);
	for (let i = 0; i < size; i++) {
		const slope = Math.cos((i / size) * Math.PI * 2) * 0.6;
		const len = Math.hypot(slope, 1);
		data.set([128, 128 + (slope / len) * 127, 128 + (1 / len) * 127, 255], i * 4);
	}
	const texture = new THREE.DataTexture(data, 1, size);
	texture.wrapS = texture.wrapT = THREE.RepeatWrapping;
	texture.repeat.set(1, 26);
	texture.needsUpdate = true;
	return texture;
}

function pcbTexture(spots: { x: number; y: number }[]) {
	const canvas = document.createElement('canvas');
	canvas.width = canvas.height = 1024;
	const ctx = canvas.getContext('2d');
	if (!ctx) throw new Error('2D canvas unavailable');
	ctx.fillStyle = '#1f5b32';
	ctx.fillRect(0, 0, 1024, 1024);
	// Shape UVs are the raw x/y, mapped onto the canvas by the texture's repeat and offset.
	const px = (x: number) => (x + 0.6) * (1024 / 1.2);
	const py = (y: number) => (0.85 - y) * (1024 / 1.7);
	ctx.strokeStyle = '#2f7a46';
	ctx.lineWidth = 5;
	for (const s of spots) {
		ctx.beginPath();
		ctx.moveTo(px(s.x), py(s.y));
		ctx.lineTo(px(s.x), py(s.y) + 30);
		ctx.lineTo(px(s.x) + 22, py(s.y) + 52);
		ctx.stroke();
	}
	ctx.fillStyle = '#c9a54a';
	for (const s of spots) {
		ctx.fillRect(px(s.x) - 26, py(s.y) - 4, 8, 8);
		ctx.fillRect(px(s.x) + 18, py(s.y) - 4, 8, 8);
	}
	const texture = new THREE.CanvasTexture(canvas);
	texture.colorSpace = THREE.SRGBColorSpace;
	texture.repeat.set(1 / 1.2, 1 / 1.7);
	texture.offset.set(0.5, 0.5);
	texture.anisotropy = 8;
	return texture;
}

function instanced(
	geometry: THREE.BufferGeometry,
	material: THREE.Material,
	at: { x: number; y: number; z: number }[],
) {
	const mesh = new THREE.InstancedMesh(geometry, material, at.length);
	const m = new THREE.Matrix4();
	at.forEach((p, i) => {
		mesh.setMatrixAt(i, m.makeTranslation(p.x, p.y, p.z));
	});
	return mesh;
}

function screw(material: THREE.Material) {
	const group = new THREE.Group();
	const parts: [THREE.BufferGeometry, number][] = [
		[new THREE.CylinderGeometry(0.042, 0.042, 0.024, 32), -0.012],
		[new THREE.CylinderGeometry(0.056, 0.056, 0.006, 32), 0.003],
		[new THREE.CylinderGeometry(0.014, 0.012, 0.15, 16), 0.081],
	];
	for (const [geometry, z] of parts) {
		const mesh = new THREE.Mesh(geometry, material);
		mesh.rotation.x = Math.PI / 2;
		mesh.position.z = z;
		group.add(mesh);
	}
	for (let i = 0; i < 9; i++) {
		const ring = new THREE.Mesh(new THREE.TorusGeometry(0.0145, 0.0035, 6, 20), material);
		ring.position.z = 0.03 + i * 0.013;
		group.add(ring);
	}
	return group;
}

function buildParts(cupList: { x: number; y: number; r: number }[]) {
	const parts = new Map<string, THREE.Group>();
	const add = (id: string, ...objects: THREE.Object3D[]) => {
		const group = new THREE.Group();
		group.userData.partId = id;
		group.add(...objects);
		parts.set(id, group);
	};

	const plastic = new THREE.MeshStandardMaterial({ color: 0x2b2e31, roughness: 0.72 });
	const flangeOutline = inset(OUTLINE, -0.06);
	const holeRing = inset(OUTLINE, -0.025);
	const screwHoles: V2[] = holeRing.flatMap((p, i) => {
		const q = holeRing[(i + 1) % holeRing.length];
		return [0.3, 0.7].map((t): V2 => [p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t]);
	});
	const innerWall = rounded(new THREE.Path(), inset(OUTLINE, 0.035), 0.07);
	const flange = rounded(new THREE.Shape(), flangeOutline, 0.12);
	flange.holes.push(innerWall, ...screwHoles.map(([x, y]) => hole(x, y, 0.016)));
	const walls = rounded(new THREE.Shape(), OUTLINE, 0.1);
	walls.holes.push(rounded(new THREE.Path(), inset(OUTLINE, 0.035), 0.07));
	const back = rounded(new THREE.Shape(), OUTLINE, 0.1);
	const connector = new THREE.Mesh(new THREE.BoxGeometry(0.17, 0.26, 0.14), plastic);
	connector.position.set(-0.08, 0.05, -0.45);
	const socket = new THREE.Mesh(
		new THREE.BoxGeometry(0.12, 0.2, 0.02),
		new THREE.MeshStandardMaterial({ color: 0x0c0c0d, roughness: 0.9 }),
	);
	socket.position.set(-0.08, 0.05, -0.525);
	// The PCB rests on these, one under each of its mounting holes.
	const bosses = PCB_HOLES.map(([x, y]) => {
		const boss = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.034, 0.05, 20), plastic);
		boss.rotation.x = Math.PI / 2;
		boss.position.set(x, y, -0.325);
		return boss;
	});
	add(
		'housing',
		new THREE.Mesh(extrude(back, 0.03, -0.38), plastic),
		new THREE.Mesh(extrude(walls, 0.34, -0.36), plastic),
		new THREE.Mesh(extrude(flange, 0.035, -0.055), plastic),
		connector,
		socket,
		...bosses,
	);

	const steel = new THREE.MeshStandardMaterial({
		color: 0x1b1c1e,
		metalness: 0.7,
		roughness: 0.32,
	});
	add(
		'fasteners',
		...[screwHoles[0], screwHoles[3], screwHoles[6]].map(([x, y]) => {
			const s = screw(steel);
			s.position.set(x, y, -0.058);
			return s;
		}),
	);

	const board = rounded(new THREE.Shape(), inset(OUTLINE, 0.06), 0.06);
	board.holes.push(...PCB_HOLES.map(([x, y]) => hole(x, y, 0.02)));
	const pcbMaterial = new THREE.MeshStandardMaterial({
		map: pcbTexture(cupList),
		roughness: 0.45,
		metalness: 0.05,
	});
	const ledBody = new THREE.MeshStandardMaterial({ color: 0xeeeae0, roughness: 0.35 });
	const ledLens = new THREE.MeshStandardMaterial({
		color: 0xffe2a0,
		roughness: 0.2,
		emissive: 0xffd8a8,
		emissiveIntensity: 0,
	});
	const pcbZ = -0.3;
	const chips = [
		[-0.22, -0.12],
		[0.08, 0.1],
		[0.3, -0.16],
	].map(([x, y]) => {
		const chip = new THREE.Mesh(
			new THREE.BoxGeometry(0.075, 0.055, 0.014),
			new THREE.MeshStandardMaterial({ color: 0x111111, roughness: 0.5 }),
		);
		chip.position.set(x, y, pcbZ + 0.023);
		return chip;
	});
	add(
		'pcb',
		new THREE.Mesh(extrude(board, 0.016, pcbZ), pcbMaterial),
		instanced(
			new THREE.BoxGeometry(0.046, 0.046, 0.014),
			ledBody,
			cupList.map((c) => ({ ...c, z: pcbZ + 0.023 })),
		),
		instanced(
			new THREE.CylinderGeometry(0.015, 0.015, 0.006, 20).rotateX(Math.PI / 2),
			ledLens,
			cupList.map((c) => ({ ...c, z: pcbZ + 0.032 })),
		),
		...chips,
	);

	const chrome = new THREE.MeshStandardMaterial({
		color: 0xffffff,
		metalness: 1,
		roughness: 0.07,
		side: THREE.DoubleSide,
	});
	const reflectorZ = -0.16;
	const plate = rounded(new THREE.Shape(), inset(OUTLINE, 0.055), 0.07);
	plate.holes.push(...cupList.map((c) => hole(c.x, c.y, c.r)));
	const cupMeshes = [0.042, 0.075].map((r) => {
		const depth = r * 1.5;
		const profile = Array.from({ length: 14 }, (_, i) => {
			const t = i / 13;
			return new THREE.Vector2(0.016 + (r - 0.016) * Math.sqrt(t), depth * t);
		});
		const geometry = new THREE.LatheGeometry(profile, 32).rotateX(Math.PI / 2);
		const at = cupList
			.filter((c) => c.r === r)
			.map((c) => ({ x: c.x, y: c.y, z: reflectorZ + 0.06 - depth }));
		return instanced(geometry, chrome, at);
	});
	add('reflector', new THREE.Mesh(extrude(plate, 0.06, reflectorZ), chrome), ...cupMeshes);

	const loop = rounded(new THREE.Shape(), inset(OUTLINE, 0.012), 0.09).getSpacedPoints(240);
	const curve = new THREE.CatmullRomCurve3(
		loop.slice(0, -1).map((p) => new THREE.Vector3(p.x, p.y, -0.005)),
		true,
	);
	add(
		'gasket',
		new THREE.Mesh(
			new THREE.TubeGeometry(curve, 360, 0.017, 12, true),
			new THREE.MeshStandardMaterial({ color: 0x161617, roughness: 0.95 }),
		),
	);

	const retroShape = rounded(
		new THREE.Shape(),
		[
			[RETRO.x - RETRO.w / 2, RETRO.y - RETRO.h / 2],
			[RETRO.x + RETRO.w / 2, RETRO.y - RETRO.h / 2],
			[RETRO.x + RETRO.w / 2, RETRO.y + RETRO.h / 2],
			[RETRO.x - RETRO.w / 2, RETRO.y + RETRO.h / 2],
		],
		0.025,
	);
	const retroMaterial = new THREE.MeshPhysicalMaterial({
		color: 0xb0121c,
		roughness: 0.25,
		clearcoat: 1,
		clearcoatRoughness: 0.1,
	});
	const prisms: { x: number; y: number; z: number }[] = [];
	for (let x = RETRO.x - RETRO.w / 2 + 0.02; x < RETRO.x + RETRO.w / 2 - 0.01; x += 0.024)
		for (let y = RETRO.y - RETRO.h / 2 + 0.02; y < RETRO.y + RETRO.h / 2 - 0.01; y += 0.024)
			prisms.push({ x, y, z: -0.067 });
	add(
		'retro-reflector',
		new THREE.Mesh(extrude(retroShape, 0.02, -0.06), retroMaterial),
		instanced(
			new THREE.ConeGeometry(0.0135, 0.014, 3).rotateX(-Math.PI / 2),
			retroMaterial,
			prisms,
		),
	);

	const lensMaterial = new THREE.MeshPhysicalMaterial({
		color: 0xd0121e,
		transmission: 0.92,
		roughness: 0.12,
		thickness: 0.25,
		ior: 1.49,
		attenuationColor: new THREE.Color(0x9a0010),
		attenuationDistance: 0.35,
		clearcoat: 1,
		clearcoatRoughness: 0.04,
		normalMap: ribbedNormalMap(),
		normalScale: new THREE.Vector2(0.35, 0.35),
		emissive: 0xff1020,
		emissiveIntensity: 0,
	});
	add(
		'lens',
		// The bevel grows the face by 0.07, so start inset to land on the housing flange.
		new THREE.Mesh(
			extrude(rounded(new THREE.Shape(), inset(OUTLINE, 0.01), 0.1), 0.04, 0.07, 0.07),
			lensMaterial,
		),
	);

	return parts;
}

export function createLampScene(
	host: HTMLElement,
	labels: LampLabel[],
	onSelect: (id: string | null) => void,
	onHover: (id: string | null) => void,
): LampScene {
	const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
	renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
	renderer.toneMapping = THREE.ACESFilmicToneMapping;
	renderer.toneMappingExposure = 1.05;
	renderer.domElement.style.display = 'block';
	host.appendChild(renderer.domElement);

	const labelRenderer = new CSS2DRenderer();
	Object.assign(labelRenderer.domElement.style, { position: 'absolute', inset: '0' });
	labelRenderer.domElement.style.pointerEvents = 'none';
	host.appendChild(labelRenderer.domElement);

	const scene = new THREE.Scene();
	const pmrem = new THREE.PMREMGenerator(renderer);
	scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
	const key = new THREE.DirectionalLight(0xffffff, 1.4);
	key.position.set(-3, 4, 5);
	scene.add(key);

	const camera = new THREE.PerspectiveCamera(17, 1, 0.1, 60);
	camera.position.copy(CAMERA_HOME);
	const controls = new OrbitControls(camera, renderer.domElement);
	controls.target.copy(TARGET_HOME);
	controls.enableDamping = true;
	controls.dampingFactor = 0.08;
	controls.minDistance = 2.5;
	controls.maxDistance = 18;
	// Sway gently around the home view until someone takes the controls.
	let idle = true;
	let swayStart = performance.now();
	const home = new THREE.Spherical().setFromVector3(CAMERA_HOME.clone().sub(TARGET_HOME));
	const sway = new THREE.Spherical();
	controls.addEventListener('start', () => {
		idle = false;
	});

	const parts = buildParts(cups());
	const lamp = new THREE.Group();
	const labelObjects = new Map<string, CSS2DObject>();
	let hovered: string | null = null;
	const hover = (id: string | null) => {
		if (id === hovered) return;
		hovered = id;
		renderer.domElement.style.cursor = id ? 'pointer' : '';
		onHover(id);
	};
	for (const [id, group] of parts) {
		lamp.add(group);
		const info = labels.find((l) => l.id === id);
		if (!info) continue;
		const el = document.createElement('button');
		el.type = 'button';
		el.className = 'lamp3d-label';
		el.innerHTML = `<span class="lamp3d-label-no"></span><span class="lamp3d-label-name"></span>`;
		el.children[0].textContent = info.number;
		el.children[1].textContent = info.name;
		el.addEventListener('click', () => onSelect(id));
		el.addEventListener('pointerenter', () => hover(id));
		el.addEventListener('pointerleave', () => hover(null));
		const label = new CSS2DObject(el);
		const box = new THREE.Box3().setFromObject(group);
		label.position.set((box.min.x + box.max.x) / 2, box.max.y + 0.1, (box.min.z + box.max.z) / 2);
		group.add(label);
		labelObjects.set(id, label);
	}
	scene.add(lamp);

	const materials = new Map<string, THREE.Material[]>();
	for (const [id, group] of parts) {
		const list = new Set<THREE.Material>();
		group.traverse((o) => {
			if (o instanceof THREE.Mesh) list.add(o.material as THREE.Material);
		});
		materials.set(id, [...list]);
	}

	let explode = 0;
	let explodeTarget = 0;
	let selected: string | null = null;

	function applySelection() {
		for (const [id, list] of materials) {
			const ghost = selected !== null && id !== selected;
			for (const m of list) {
				m.transparent = ghost;
				m.opacity = ghost ? 0.12 : 1;
				m.depthWrite = !ghost;
				m.needsUpdate = true;
			}
		}
	}

	const raycaster = new THREE.Raycaster();
	const pointer = new THREE.Vector2();
	/** The visible part under the pointer, if any. */
	const partAt = (e: PointerEvent) => {
		const rect = renderer.domElement.getBoundingClientRect();
		pointer.set(
			((e.clientX - rect.left) / rect.width) * 2 - 1,
			-((e.clientY - rect.top) / rect.height) * 2 + 1,
		);
		raycaster.setFromCamera(pointer, camera);
		const visible = [...parts]
			.filter(([id]) => selected === null || id === selected)
			.map(([, g]) => g);
		const hit = raycaster.intersectObjects(visible, true)[0];
		let o: THREE.Object3D | null = hit?.object ?? null;
		while (o && !o.userData.partId) o = o.parent;
		return (o?.userData.partId as string | undefined) ?? null;
	};
	let down: { x: number; y: number } | null = null;
	const onDown = (e: PointerEvent) => {
		down = { x: e.clientX, y: e.clientY };
	};
	const onUp = (e: PointerEvent) => {
		if (!down || Math.hypot(e.clientX - down.x, e.clientY - down.y) > 4) return;
		onSelect(partAt(e));
	};
	// No hover while dragging, so the card does not chase a rotating model.
	const onMove = (e: PointerEvent) => hover(e.buttons ? null : partAt(e));
	const onLeave = () => hover(null);
	renderer.domElement.addEventListener('pointerdown', onDown);
	renderer.domElement.addEventListener('pointerup', onUp);
	renderer.domElement.addEventListener('pointermove', onMove);
	renderer.domElement.addEventListener('pointerleave', onLeave);

	let inset = 0;
	const resize = () => {
		const { clientWidth: w, clientHeight: h } = host;
		if (!w || !h) return;
		renderer.setSize(w, h);
		labelRenderer.setSize(w, h);
		camera.aspect = w / h;
		// Keep the exploded stack in frame on narrow viewports.
		// An inset frame leaves the model less room to sway, so it gets some margin.
		const aspect = (w * (1 - inset) * (inset ? 0.85 : 1)) / h;
		camera.fov = aspect < 1.6 ? 17 * (1.6 / aspect) ** 0.8 : 17;
		if (inset) camera.setViewOffset(w, h, (-w * inset) / 2, 0, w, h);
		else camera.clearViewOffset();
		camera.updateProjectionMatrix();
	};
	const observer = new ResizeObserver(resize);
	observer.observe(host);
	resize();

	let frame = 0;
	const loop = () => {
		frame = requestAnimationFrame(loop);
		explode += (explodeTarget - explode) * 0.08;
		const e = explode < 0.5 ? 4 * explode ** 3 : 1 - (-2 * explode + 2) ** 3 / 2;
		for (const [id, group] of parts) group.position.z = (SPREAD[id] ?? 0) * e;
		const labelOpacity = String(Math.min(1, Math.max(0, (explode - 0.55) / 0.35)));
		for (const label of labelObjects.values()) label.element.style.opacity = labelOpacity;
		if (idle) {
			sway.copy(home);
			// Closer on the assembled lamp, pulling back as the stack opens.
			sway.radius = home.radius * (0.72 + 0.28 * e);
			sway.theta += Math.sin(((performance.now() - swayStart) / 1000) * 0.3) * 0.2;
			camera.position.setFromSpherical(sway).add(controls.target);
		}
		controls.update();
		renderer.render(scene, camera);
		labelRenderer.render(scene, camera);
	};
	loop();

	return {
		setExplode(value) {
			explodeTarget = value;
		},
		setSelected(id) {
			selected = id;
			applySelection();
			for (const [labelId, label] of labelObjects)
				label.element.classList.toggle('lamp3d-label-on', labelId === id);
		},
		setLit(lit) {
			for (const [id, list] of materials) {
				if (id !== 'pcb' && id !== 'lens') continue;
				for (const m of list)
					if (m instanceof THREE.MeshStandardMaterial && m.emissive.getHex() !== 0)
						m.emissiveIntensity = lit ? (id === 'lens' ? 0.35 : 4) : 0;
			}
		},
		screenPoint(id) {
			const label = labelObjects.get(id);
			if (!label) return null;
			const p = label.getWorldPosition(new THREE.Vector3()).project(camera);
			return {
				x: ((p.x + 1) / 2) * host.clientWidth,
				y: ((1 - p.y) / 2) * host.clientHeight,
			};
		},
		setInset(fraction) {
			inset = fraction;
			resize();
		},
		resetView() {
			camera.position.copy(CAMERA_HOME);
			controls.target.copy(TARGET_HOME);
			swayStart = performance.now();
			idle = true;
		},
		dispose() {
			cancelAnimationFrame(frame);
			observer.disconnect();
			controls.dispose();
			renderer.domElement.removeEventListener('pointerdown', onDown);
			renderer.domElement.removeEventListener('pointerup', onUp);
			renderer.domElement.removeEventListener('pointermove', onMove);
			renderer.domElement.removeEventListener('pointerleave', onLeave);
			scene.traverse((o) => {
				if (o instanceof THREE.Mesh) {
					o.geometry.dispose();
					const m = o.material as THREE.MeshStandardMaterial;
					m.map?.dispose();
					m.normalMap?.dispose();
					m.dispose();
				}
			});
			scene.environment?.dispose();
			pmrem.dispose();
			renderer.dispose();
			renderer.domElement.remove();
			labelRenderer.domElement.remove();
		},
	};
}
