import type { Regulation, RegulationGroup, RequirementsResult, Source } from './types';

class App {
	cases: string[] = $state([]);
	regulations: Regulation[] = $state([]);
	selectedCase = $state('');
	spec = $state('');
	image: File | null = $state(null);
	imageUrl: string | null = $state(null);
	loading = $state(false);
	error = $state('');
	result: RequirementsResult | null = $state(null);
	selectedId: string | null = $state(null);

	byRegulation: RegulationGroup[] = $derived.by(() => {
		const groups = new Map<string, RegulationGroup>();
		for (const req of this.result?.requirements ?? []) {
			const reg = req.source.regulation;
			let g = groups.get(reg);
			if (!g) {
				g = { regulation: reg, title: this.regulationTitle(reg), count: 0, requirements: [] };
				groups.set(reg, g);
			}
			g.requirements.push(req);
			g.count++;
		}
		return [...groups.values()];
	});

	selected = $derived(this.result?.requirements.find((r) => r.id === this.selectedId) ?? null);

	async init() {
		if (this.cases.length) return;
		[this.cases, this.regulations] = await Promise.all([
			fetch('/api/cases').then((r) => r.json()),
			fetch('/api/regulations').then((r) => r.json()),
		]);
	}

	async loadCase(name: string) {
		this.selectedCase = name;
		if (!name) return;
		const data = await fetch(`/api/cases/${name}`).then((r) => r.json());
		this.spec = data.spec;
		this.imageUrl = data.image_url;
		this.image = null;
	}

	async setSpecFile(file: File | null | undefined) {
		if (file) this.spec = await file.text();
	}

	setImageFile(file: File | null | undefined) {
		this.image = file ?? null;
		this.imageUrl = this.image ? URL.createObjectURL(this.image) : null;
	}

	async submit() {
		this.loading = true;
		this.error = '';
		try {
			const body = new FormData();
			body.set('spec', this.spec);
			if (this.image) body.set('image', this.image);
			else if (this.imageUrl) {
				const blob = await fetch(this.imageUrl).then((r) => r.blob());
				body.set('image', blob, 'exploded_view.png');
			}
			const res = await fetch('/api/requirements', { method: 'POST', body });
			if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
			this.result = await res.json();
			this.selectedId = null;
		} catch (err) {
			this.error = String(err);
		} finally {
			this.loading = false;
		}
	}

	async demo() {
		await this.init();
		await this.loadCase('dev-rear-lamp');
		await this.submit();
	}

	select(id: string | null) {
		this.selectedId = id;
	}

	regulationTitle(reg: string) {
		return this.regulations.find((r) => r.regulation === reg)?.title ?? '';
	}

	pdfUrl({ regulation, version, page }: Source) {
		const entry = this.regulations.find((r) => r.regulation === regulation);
		const v = entry?.versions.find((v) => v.version_label === version);
		if (!entry || !v) return null;
		const dir = regulation.replace(' ', '_');
		return `/pdfs/${dir}/${v.role}/${v.files[0].name}#page=${page}`;
	}

	download() {
		const blob = new Blob([JSON.stringify(this.result, null, 2)], { type: 'application/json' });
		const a = document.createElement('a');
		a.href = URL.createObjectURL(blob);
		a.download = 'requirements.json';
		a.click();
		URL.revokeObjectURL(a.href);
	}
}

export const app = new App();
