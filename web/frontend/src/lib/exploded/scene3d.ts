// The 3D exploded view's scene, shared by every product: renderer, controls, environment,
// part labels, hover, selection, focus and the explode tween. A product model supplies the
// parts, how far each one moves when exploded, the camera and which parts light up.

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { CSS2DObject, CSS2DRenderer } from 'three/addons/renderers/CSS2DRenderer.js';

export interface PartLabel {
	id: string;
	number: string;
	name: string;
}

export interface ProductModel {
	/** One group per part, keyed by part id, in assembled position. */
	parts: Map<string, THREE.Group>;
	/** Where each part moves to, relative to assembled, at full explode. */
	spread: Record<string, THREE.Vector3>;
	camera: THREE.Vector3;
	target: THREE.Vector3;
	/** Vertical field of view on a wide viewport. */
	fov: number;
	minDistance: number;
	maxDistance: number;
	/** Emissive intensity per part when the lights are on. */
	glow: Record<string, number>;
}

export interface ExplodedScene {
	setExplode(value: number): void;
	setSelected(id: string | null): void;
	/** Isolates a part and flies the camera in to it. */
	focus(id: string, ms: number): void;
	setLit(lit: boolean): void;
	/** Keeps this share of the width, from the left, clear of the model. */
	setInset(fraction: number): void;
	/** Where a part's label sits in the view, in pixels from its top left. */
	screenPoint(id: string): { x: number; y: number } | null;
	resetView(): void;
	dispose(): void;
}

export function createExplodedScene(
	host: HTMLElement,
	model: ProductModel,
	labels: PartLabel[],
	onSelect: (id: string | null) => void,
	onHover: (id: string | null) => void,
): ExplodedScene {
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

	const camera = new THREE.PerspectiveCamera(model.fov, 1, 0.1, 60);
	camera.position.copy(model.camera);
	const controls = new OrbitControls(camera, renderer.domElement);
	controls.target.copy(model.target);
	controls.enableDamping = true;
	controls.dampingFactor = 0.08;
	controls.minDistance = model.minDistance;
	controls.maxDistance = model.maxDistance;
	// Sway gently around the home view until someone takes the controls.
	let idle = true;
	let swayStart = performance.now();
	const home = new THREE.Spherical().setFromVector3(model.camera.clone().sub(model.target));
	const sway = new THREE.Spherical();
	controls.addEventListener('start', () => {
		idle = false;
	});

	const { parts } = model;
	const product = new THREE.Group();
	const labelObjects = new Map<string, CSS2DObject>();
	let hovered: string | null = null;
	const hover = (id: string | null) => {
		if (id === hovered) return;
		hovered = id;
		renderer.domElement.style.cursor = id ? 'pointer' : '';
		onHover(id);
	};
	for (const [id, group] of parts) {
		product.add(group);
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
	scene.add(product);

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
		camera.fov = aspect < 1.6 ? model.fov * (1.6 / aspect) ** 0.8 : model.fov;
		if (inset) camera.setViewOffset(w, h, (-w * inset) / 2, 0, w, h);
		else camera.clearViewOffset();
		camera.updateProjectionMatrix();
	};
	const observer = new ResizeObserver(resize);
	observer.observe(host);
	resize();

	let flight: {
		start: number;
		ms: number;
		fromCamera: THREE.Vector3;
		toCamera: THREE.Vector3;
		fromTarget: THREE.Vector3;
		toTarget: THREE.Vector3;
	} | null = null;

	const none = new THREE.Vector3();
	let frame = 0;
	const loop = () => {
		frame = requestAnimationFrame(loop);
		explode += (explodeTarget - explode) * 0.08;
		const e = explode < 0.5 ? 4 * explode ** 3 : 1 - (-2 * explode + 2) ** 3 / 2;
		for (const [id, group] of parts)
			group.position.copy(model.spread[id] ?? none).multiplyScalar(e);
		const labelOpacity = String(Math.min(1, Math.max(0, (explode - 0.55) / 0.35)));
		for (const label of labelObjects.values()) label.element.style.opacity = labelOpacity;
		if (flight) {
			const t = Math.min(1, (performance.now() - flight.start) / flight.ms);
			const k = 1 - (1 - t) ** 3;
			camera.position.lerpVectors(flight.fromCamera, flight.toCamera, k);
			controls.target.lerpVectors(flight.fromTarget, flight.toTarget, k);
			for (const label of labelObjects.values()) label.element.style.opacity = String(1 - k);
		} else if (idle) {
			sway.copy(home);
			// Closer on the assembled product, pulling back as it opens.
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
		focus(id, ms) {
			const group = parts.get(id);
			if (!group) return;
			this.setSelected(id);
			idle = false;
			controls.enabled = false;
			const toTarget = new THREE.Box3().setFromObject(group).getCenter(new THREE.Vector3());
			// Same viewing angle, a third of the distance.
			const offset = camera.position.clone().sub(controls.target).multiplyScalar(0.35);
			flight = {
				start: performance.now(),
				ms,
				fromCamera: camera.position.clone(),
				toCamera: toTarget.clone().add(offset),
				fromTarget: controls.target.clone(),
				toTarget,
			};
		},
		setLit(lit) {
			for (const [id, list] of materials) {
				const glow = model.glow[id];
				if (glow === undefined) continue;
				for (const m of list)
					if (m instanceof THREE.MeshStandardMaterial && m.emissive.getHex() !== 0)
						m.emissiveIntensity = lit ? glow : 0;
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
			camera.position.copy(model.camera);
			controls.target.copy(model.target);
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
