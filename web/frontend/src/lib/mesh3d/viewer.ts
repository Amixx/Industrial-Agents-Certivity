import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

export type Part = {
	id: string;
	name: string;
	file: string | null;
	order: number;
	offset: [number, number, number];
	requirementIds: string[];
	crop: string;
};
export type Manifest = {
	caseId: string;
	mapping: string;
	geometry: string;
	parts: Part[];
	requirements: {
		id: string;
		text: string;
		source: { regulation: string; page: number; paragraph: string };
	}[];
};

export function createViewer(
	container: HTMLElement,
	parts: Part[],
	onSelect: (id: string) => void,
	onHover: (id: string | null) => void,
) {
	const scene = new THREE.Scene();
	scene.background = new THREE.Color('#ffffff');
	const camera = new THREE.OrthographicCamera(-6, 6, 2.7, -2.7, 0.01, 100);
	const renderer = new THREE.WebGLRenderer({ antialias: true });
	renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
	renderer.outputColorSpace = THREE.SRGBColorSpace;
	renderer.domElement.setAttribute(
		'aria-label',
		'3D rear lamp parts. Drag to orbit, scroll to zoom. Use the part buttons to select with a keyboard.',
	);
	container.appendChild(renderer.domElement);
	const controls = new OrbitControls(camera, renderer.domElement);
	controls.enableDamping = true;
	controls.minZoom = 0.3;
	controls.maxZoom = 4;
	scene.add(new THREE.HemisphereLight('#ffffff', '#77938e', 1.4));
	const key = new THREE.DirectionalLight('#ffffff', 2);
	key.position.set(-3, 6, 7);
	scene.add(key);
	const fill = new THREE.DirectionalLight('#ffffff', 0.7);
	fill.position.set(4, 0, -5);
	scene.add(fill);
	const groups = new Map<string, THREE.Group>();
	const materials = new Map<string, THREE.MeshStandardMaterial>();
	const loader = new GLTFLoader();
	let disposed = false;
	let selected: string | null = null;
	let hovered: string | null = null;
	let explosion = 1;
	let pointerDown = new THREE.Vector2();
	const raycaster = new THREE.Raycaster();
	const pointer = new THREE.Vector2();

	function colors() {
		for (const [id, material] of materials) {
			material.color.set(id === selected ? '#79f2de' : id === hovered ? '#b1d7d0' : '#9da7a2');
		}
	}
	function place() {
		const center =
			(Math.min(...parts.map((part) => part.offset[2])) +
				Math.max(...parts.map((part) => part.offset[2]))) /
			2;
		for (const part of parts) {
			const group = groups.get(part.id);
			if (group)
				group.position.set(
					part.offset[0] * explosion,
					part.offset[1] * explosion,
					(part.order - (parts.length - 1) / 2) * 0.17 + (part.offset[2] - center) * explosion,
				);
		}
	}
	function release(group: THREE.Object3D) {
		group.traverse((child) => {
			if (child instanceof THREE.Mesh) {
				child.geometry.dispose();
				const list = Array.isArray(child.material) ? child.material : [child.material];
				for (const material of list) {
					for (const value of Object.values(material)) {
						if (value instanceof THREE.Texture) value.dispose();
					}
					material.dispose();
				}
			}
		});
	}
	const ready = Promise.all(
		parts
			.filter((part) => part.file)
			.map(async (part) => {
				const gltf = await loader.loadAsync(`/mesh3d/dev-rear-lamp/${part.file}`);
				const model = gltf.scene;
				if (disposed) {
					release(model);
					return;
				}
				const bounds = new THREE.Box3().setFromObject(model);
				const center = bounds.getCenter(new THREE.Vector3());
				const size = bounds.getSize(new THREE.Vector3());
				model.position.sub(center);
				const group = new THREE.Group();
				group.add(model);
				group.scale.setScalar(3.3 / Math.max(size.x, size.y, size.z));
				const material = new THREE.MeshStandardMaterial({
					color: '#9da7a2',
					roughness: 0.8,
					metalness: 0,
					side: THREE.DoubleSide,
				});
				model.traverse((child) => {
					if (child instanceof THREE.Mesh) {
						const original = Array.isArray(child.material) ? child.material : [child.material];
						for (const item of original) {
							for (const value of Object.values(item))
								if (value instanceof THREE.Texture) value.dispose();
							item.dispose();
						}
						child.material = material;
						child.userData.partId = part.id;
					}
				});
				groups.set(part.id, group);
				materials.set(part.id, material);
				scene.add(group);
				place();
				colors();
			}),
	);
	function reset() {
		camera.position.set(10, 1.6, 7);
		camera.zoom = 1;
		camera.updateProjectionMatrix();
		controls.target.set(0, 0, 0);
		controls.update();
	}
	reset();
	function hit(event: PointerEvent): string | null {
		const rect = renderer.domElement.getBoundingClientRect();
		pointer.set(
			((event.clientX - rect.left) / rect.width) * 2 - 1,
			(-(event.clientY - rect.top) / rect.height) * 2 + 1,
		);
		raycaster.setFromCamera(pointer, camera);
		return (
			raycaster.intersectObjects([...groups.values()], true)[0]?.object.userData.partId ?? null
		);
	}
	function move(event: PointerEvent) {
		hovered = hit(event);
		renderer.domElement.style.cursor = hovered ? 'pointer' : 'grab';
		onHover(hovered);
		colors();
	}
	function leave() {
		hovered = null;
		onHover(null);
		colors();
	}
	function down(event: PointerEvent) {
		pointerDown = new THREE.Vector2(event.clientX, event.clientY);
	}
	function up(event: PointerEvent) {
		if (pointerDown.distanceTo(new THREE.Vector2(event.clientX, event.clientY)) > 5) return;
		const id = hit(event);
		if (id) onSelect(id);
	}
	renderer.domElement.addEventListener('pointermove', move);
	renderer.domElement.addEventListener('pointerleave', leave);
	renderer.domElement.addEventListener('pointerdown', down);
	renderer.domElement.addEventListener('pointerup', up);
	const observer = new ResizeObserver(() => {
		const { width, height } = container.getBoundingClientRect();
		renderer.setSize(width, height);
		const aspect = width / height;
		const halfHeight = Math.max(2.7, 6 / aspect);
		camera.left = -halfHeight * aspect;
		camera.right = halfHeight * aspect;
		camera.top = halfHeight;
		camera.bottom = -halfHeight;
		camera.updateProjectionMatrix();
	});
	observer.observe(container);
	renderer.setAnimationLoop(() => {
		controls.update();
		renderer.render(scene, camera);
	});
	return {
		ready,
		reset,
		explode(value: number) {
			explosion = value;
			place();
		},
		select(id: string | null) {
			selected = id;
			colors();
		},
		dispose() {
			disposed = true;
			observer.disconnect();
			renderer.setAnimationLoop(null);
			controls.dispose();
			renderer.domElement.removeEventListener('pointermove', move);
			renderer.domElement.removeEventListener('pointerleave', leave);
			renderer.domElement.removeEventListener('pointerdown', down);
			renderer.domElement.removeEventListener('pointerup', up);
			for (const group of groups.values()) release(group);
			renderer.dispose();
			renderer.domElement.remove();
		},
	};
}
