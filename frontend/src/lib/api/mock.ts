import expected from './fixtures/expected.json';
import { regulationIndex, regulationTitle } from './regulations.ts';
import type {
	ApiClient,
	Assessment,
	PipelineEvent,
	Profile,
	RegulationDecision,
	RegulationUpdate,
	Requirement,
	RequirementChange
} from './types.ts';

const fixtureRequirements: Requirement[] = expected.requirements;
const STORAGE_KEY = 'sudo.assessments';
const memory = new Map<string, Assessment>();

function load(): Assessment[] {
	try {
		const raw = localStorage.getItem(STORAGE_KEY);
		if (raw) return JSON.parse(raw);
	} catch {
		/* storage unavailable: fall through to the in-memory copy */
	}
	return [...memory.values()];
}

function save(assessment: Assessment) {
	memory.set(assessment.id, assessment);
	const all = [assessment, ...load().filter((a) => a.id !== assessment.id)];
	try {
		localStorage.setItem(STORAGE_KEY, JSON.stringify(all));
	} catch {
		/* storage full or blocked: the in-memory copy still serves this session */
	}
}

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

function section(spec: string, heading: string) {
	const match = spec.match(new RegExp(`^##\\s+${heading}\\s*$([\\s\\S]*?)(?=^##\\s|$(?![\\s\\S]))`, 'im'));
	return match?.[1].trim() ?? '';
}

function bullets(text: string) {
	return text
		.split('\n')
		.map((l) => l.match(/^\s*[-*]\s+(.*)$/)?.[1].trim())
		.filter((l): l is string => !!l);
}

function firstLine(text: string) {
	return text.split('\n').find((l) => l.trim())?.trim() ?? '';
}

export function deriveProfile(spec: string): Profile {
	const materials = section(spec, 'Materials')
		.split('\n')
		.filter((l) => l.trim().startsWith('|') && !/^\|\s*-/.test(l.trim()))
		.slice(1)
		.map((l) => {
			const [part, material] = l.split('|').slice(1, 3).map((c) => c.trim());
			return `${part}: ${material}`;
		});
	return {
		productType: firstLine(section(spec, 'Product Type')).replace(/\s+/g, ' '),
		vehicleCategory: firstLine(section(spec, 'Vehicle Category')),
		parts: bullets(section(spec, 'Main Parts')),
		functions: bullets(section(spec, 'Functions?')),
		materials
	};
}

const included: [string, string, string][] = [
	[
		'UN R48',
		'9.3.0',
		'Installation of lighting and light-signalling devices: the rear lamp is a light-signalling device installed on an M1 vehicle.'
	],
	[
		'UN R148',
		'1.6.0',
		'Device approval for the rear position, stop and reversing lamp functions the product combines.'
	],
	[
		'UN R150',
		'1.2.1',
		'The housing integrates a rear retro-reflector (passive conspicuity), which needs device approval as a retro-reflective device.'
	],
	[
		'UN R10',
		'7.2.0',
		'LED modules on a PCB make the lamp an electrical/electronic sub-assembly (ESA), subject to EMC emission and immunity limits.'
	]
];

const excluded: [string, string][] = [
	['UN R7', 'Position and stop lamps: superseded by the consolidated R148 for new approvals.'],
	['UN R23', 'Reversing lamps: superseded by the consolidated R148 for new approvals.'],
	['UN R3', 'Retro-reflecting devices: superseded by the consolidated R150 for new approvals.'],
	['UN R6', 'Direction indicator: not a function of this product.'],
	['UN R19', 'Front fog lamp: not a function of this product.'],
	['UN R38', 'Rear fog lamp: not among the functions listed in the spec.'],
	['UN R37', 'Filament light sources: the light source is LED modules, no filament bulbs.'],
	[
		'UN R128',
		'Replaceable LED light sources only: the LED modules here are non-replaceable and approved as part of the lamp under R148.'
	],
	['UN R149', 'Road illumination devices (headlamps): the rear lamp does not illuminate the road ahead.'],
	['UN R123', 'Adaptive front-lighting systems: front lighting only.'],
	[
		'UN R104',
		'Retro-reflective marking tape for heavy vehicles and trailers (M2, M3, N, O): not M1, and not a marking product.'
	],
	['UN R53', 'Lighting installation for L3 motorcycles: the target vehicle is M1.'],
	['UN R43', 'Safety glazing: the PMMA outer lens is a lamp lens, not vehicle glazing.'],
	['UN R26', 'External projections: assessed on the whole vehicle, not on a component approval.']
];

function decisions(requirements: Requirement[]): RegulationDecision[] {
	const count = (reg: string) => requirements.filter((r) => r.source.regulation === reg).length;
	const base = (reg: string) =>
		regulationIndex.find((r) => r.regulation === reg)?.versions.find((v) => v.role === 'base')
			?.version_label ?? '';
	return [
		...included.map(([regulation, version, reason]) => ({
			regulation,
			version,
			title: regulationTitle(regulation),
			included: true,
			reason,
			requirementCount: count(regulation)
		})),
		...excluded.map(([regulation, reason]) => ({
			regulation,
			version: base(regulation),
			title: regulationTitle(regulation),
			included: false,
			reason,
			requirementCount: 0
		}))
	];
}

const paragraphCounts: Record<string, number> = {
	'UN R48': 88,
	'UN R148': 61,
	'UN R150': 37,
	'UN R10': 28
};

type UpdateDef = {
	regulation: string;
	fromVersion: string;
	toVersion: string;
	changes: (Omit<RequirementChange, 'oldText'> & { newId?: string })[];
};

const updateDefs: UpdateDef[] = [
	{
		regulation: 'UN R48',
		fromVersion: '9.3.0',
		toVersion: '9.4.0',
		changes: [
			{
				requirementId: 'G-0057',
				change: 'modified',
				newText:
					'For all light-signalling devices, including those mounted on the side panels, the reference axis of the lamp when fitted to the vehicle shall be parallel to the bearing plane of the vehicle on the road, with a tolerance of ±3° allowed in each direction; for lamps mounted on movable components this applies in every fixed position of use.',
				reason: 'Supplement clarifies how the alignment tolerance applies to lamps on movable components such as tailgates.',
				source: { page: 19, paragraph: '5.3' }
			},
			{
				requirementId: 'G-0060',
				change: 'modified',
				newText:
					'For all light-signalling devices, including those mounted on the side panels, any specific instructions as regards fitting laid down by the manufacturer and stated in the communication form shall be complied with.',
				reason: 'Fitting instructions must now be documented in the type-approval communication form.',
				source: { page: 19, paragraph: '5.3' }
			},
			{
				requirementId: null,
				newId: 'U-R48-01',
				change: 'added',
				newText:
					'Where a stop lamp and a rear position lamp are reciprocally incorporated, the ratio between their luminous intensities shall be at least 5:1 in the area of the reference axis.',
				reason: 'New paragraph on reciprocally incorporated rear position and stop functions.',
				source: { page: 21, paragraph: '5.11.3' }
			}
		]
	},
	{
		regulation: 'UN R148',
		fromVersion: '1.6.0',
		toVersion: '1.7.0',
		changes: [
			{
				requirementId: 'G-0163',
				change: 'modified',
				newText: 'The value for ‘a’ shall be at least 4 mm with regard to the size of the approval marking.',
				reason: 'Minimum marking size reduced to suit compact lamp designs.',
				source: { page: 6, paragraph: '3.3.1.2' }
			},
			{
				requirementId: 'G-0164',
				change: 'removed',
				reason: 'Sequential-number placement now governed by the Unique Identifier provisions of the 1958 Agreement.',
				source: { page: 7, paragraph: '3.3.2.2' }
			},
			{
				requirementId: 'G-0167',
				change: 'modified',
				newText:
					'In the case of front or rear position lamps, front or rear end-outline marker lamps and side-marker lamps, the arrow shall be directed outwards from the vehicle.',
				reason: 'Side-marker lamps added to the arrow-direction rule.',
				source: { page: 7, paragraph: '3.3.2.5.1.1' }
			}
		]
	},
	{
		regulation: 'UN R10',
		fromVersion: '7.2.0',
		toVersion: '7.3.0',
		changes: [
			{
				requirementId: 'G-0130',
				change: 'modified',
				newText:
					'When measurements are made using the method described in Annex 7, in the 400 to 2,500 MHz frequency band the limit shall remain constant at 63 dB microvolts/m.',
				reason: 'Radiated-emission measurement range extended from 1 GHz to 2.5 GHz.',
				source: { page: 10, paragraph: '6.5.2.1' }
			},
			{
				requirementId: null,
				newId: 'U-R10-01',
				change: 'added',
				newText:
					'The ESA shall be tested for immunity to transient disturbances conducted along 12 V and 24 V supply lines using the method described in Annex 10.',
				reason: 'Conducted transient immunity test made mandatory for all ESAs.',
				source: { page: 11, paragraph: '6.8.1' }
			}
		]
	}
];

function appliedKey(id: string) {
	return `sudo.applied.${id}`;
}

function appliedFor(id: string): string[] {
	try {
		return JSON.parse(localStorage.getItem(appliedKey(id)) ?? '[]');
	} catch {
		return [];
	}
}

function markApplied(id: string, regulation: string) {
	try {
		localStorage.setItem(appliedKey(id), JSON.stringify([...appliedFor(id), regulation]));
	} catch {
		/* storage unavailable */
	}
}

function updatesFor(assessment: Assessment): RegulationUpdate[] {
	const applied = appliedFor(assessment.id);
	const original = new Map(fixtureRequirements.map((r) => [r.id, r]));
	return updateDefs
		.filter((def) => assessment.regulations.some((d) => d.included && d.regulation === def.regulation))
		.map((def) => ({
			regulation: def.regulation,
			fromVersion: def.fromVersion,
			toVersion: def.toVersion,
			applied: applied.includes(def.regulation),
			changes: def.changes.map(({ newId: _, ...c }) => ({
				...c,
				oldText: c.requirementId ? original.get(c.requirementId)?.text : undefined
			}))
		}));
}

function readDataUrl(blob: Blob): Promise<string> {
	return new Promise((resolve, reject) => {
		const reader = new FileReader();
		reader.onload = () => resolve(reader.result as string);
		reader.onerror = () => reject(reader.error);
		reader.readAsDataURL(blob);
	});
}

export const mock: ApiClient = {
	async runAssessment(spec, image, onEvent, caseName) {
		const emit = (event: PipelineEvent) => onEvent(event);
		const requirements = fixtureRequirements.map((r) => ({ ...r, source: { ...r.source } }));

		emit({ step: 'profile', message: 'Reading spec', progress: 0.03 });
		await sleep(600);
		const profile = deriveProfile(spec);
		emit({
			step: 'profile',
			message: `Reading spec: ${profile.parts.length} parts, ${profile.functions.length} functions, ${profile.materials.length} materials`,
			progress: 0.15,
			partial: { profile }
		});
		await sleep(700);

		emit({
			step: 'selection',
			message: `Screening ${regulationIndex.length} regulations against the profile`,
			progress: 0.22,
			partial: { profile }
		});
		await sleep(800);
		const regulations = decisions([]);
		emit({
			step: 'selection',
			message: `Selected ${included.length} of ${regulationIndex.length} regulations, ${excluded.length} excluded with reasons`,
			progress: 0.38,
			partial: { profile, regulations }
		});
		await sleep(500);

		let paragraphCount = 0;
		for (const [reg, version] of included) {
			paragraphCount += paragraphCounts[reg];
			emit({
				step: 'paragraphs',
				message: `Scanning ${reg} ${version}: ${paragraphCounts[reg]} applicable paragraphs`,
				progress: 0.38 + (0.22 * paragraphCount) / 214,
				partial: { profile, regulations, paragraphCount }
			});
			await sleep(300);
		}
		emit({
			step: 'paragraphs',
			message: `Scanning ${paragraphCount} paragraphs`,
			progress: 0.6,
			partial: { profile, regulations, paragraphCount }
		});
		await sleep(400);

		const found: Requirement[] = [];
		for (const [reg] of included) {
			found.push(...requirements.filter((r) => r.source.regulation === reg));
			emit({
				step: 'requirements',
				message: `${reg}: ${found.filter((r) => r.source.regulation === reg).length} requirements extracted`,
				progress: 0.6 + (0.38 * found.length) / requirements.length,
				partial: { profile, regulations: decisions(found), paragraphCount, requirements: [...found] }
			});
			await sleep(450);
		}

		const assessment: Assessment = {
			id: crypto.randomUUID().slice(0, 8),
			createdAt: new Date().toISOString(),
			caseName,
			spec,
			imageUrl: image ? await readDataUrl(image) : undefined,
			profile,
			regulations: decisions(requirements),
			requirements,
			status: 'complete'
		};
		save(assessment);
		emit({
			step: 'done',
			message: `${requirements.length} requirements from ${included.length} regulations`,
			progress: 1,
			assessmentId: assessment.id,
			partial: { profile, regulations: assessment.regulations, paragraphCount, requirements }
		});
		return assessment;
	},

	async listAssessments() {
		return load().sort((a, b) => b.createdAt.localeCompare(a.createdAt));
	},

	async getAssessment(id) {
		return load().find((a) => a.id === id) ?? null;
	},

	async checkUpdates(id) {
		await sleep(300);
		const assessment = await this.getAssessment(id);
		return assessment ? updatesFor(assessment) : [];
	},

	async applyUpdate(id, regulation) {
		const assessment = await this.getAssessment(id);
		if (!assessment) throw new Error(`Assessment ${id} not found`);
		const def = updateDefs.find((d) => d.regulation === regulation);
		if (!def) throw new Error(`No update for ${regulation}`);
		if (appliedFor(id).includes(regulation)) return assessment;

		let requirements = assessment.requirements.map((r) =>
			r.source.regulation === regulation ? { ...r, source: { ...r.source, version: def.toVersion } } : r
		);
		for (const c of def.changes) {
			if (c.change === 'removed') requirements = requirements.filter((r) => r.id !== c.requirementId);
			if (c.change === 'modified')
				requirements = requirements.map((r) =>
					r.id === c.requirementId ? { ...r, text: c.newText ?? r.text, source: { ...r.source, ...c.source } } : r
				);
			if (c.change === 'added' && c.newId)
				requirements.push({
					id: c.newId,
					text: c.newText ?? '',
					source: { regulation, version: def.toVersion, ...c.source }
				});
		}
		const counts = (reg: string) => requirements.filter((r) => r.source.regulation === reg).length;
		const updated: Assessment = {
			...assessment,
			requirements,
			regulations: assessment.regulations.map((d) =>
				d.regulation === regulation
					? { ...d, version: def.toVersion, requirementCount: counts(regulation) }
					: d
			)
		};
		save(updated);
		markApplied(id, regulation);
		return updated;
	}
};
