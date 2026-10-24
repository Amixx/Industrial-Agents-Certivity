// Layers cut from one generated render (static/exploded/rear-lamp), so every part shares
// the same camera and lighting. Boxes are in frame pixels; `cx` is where the part sits
// along the stack once assembled, which for the housing ignores the connector on its back.

export interface ExplodedPart {
	id: string;
	name: string;
	material: string;
	check: string;
	x: number;
	y: number;
	w: number;
	h: number;
	cx?: number;
}

export interface ExplodedAssembly {
	name: string;
	base: string;
	width: number;
	height: number;
	parts: ExplodedPart[];
}

export const rearLamp: ExplodedAssembly = {
	name: 'Rear lamp',
	base: '/exploded/rear-lamp',
	width: 2752,
	height: 1072,
	parts: [
		{
			id: 'fasteners',
			name: 'Fasteners / clips',
			material: 'PA, POM or steel',
			check: 'Lamp stays aimed under vibration',
			x: 0,
			y: 281,
			w: 164,
			h: 487,
		},
		{
			id: 'housing',
			name: 'Housing',
			material: 'PP or ASA/PC',
			check: 'Reversing lamp visible to 45° outboard',
			x: 204,
			y: 0,
			w: 525,
			h: 1072,
			cx: 506,
		},
		{
			id: 'pcb',
			name: 'LED modules on PCB',
			material: 'LEDs on FR-4',
			check: 'Stop lamp: 60 to 185 cd on axis',
			x: 747,
			y: 82,
			w: 351,
			h: 974,
		},
		{
			id: 'reflector',
			name: 'Reflector',
			material: 'PC, vacuum-metallised aluminium',
			check: 'Rear position lamp: 4 to 17 cd on axis',
			x: 1136,
			y: 71,
			w: 377,
			h: 986,
		},
		{
			id: 'gasket',
			name: 'Seal / gasket',
			material: 'TPE or silicone',
			check: 'No water ingress after the spray test',
			x: 1543,
			y: 81,
			w: 414,
			h: 974,
		},
		{
			id: 'retro-reflector',
			name: 'Retro-reflector',
			material: 'PMMA, moulded prism optics',
			check: 'Reflectivity at 5° angle of incidence',
			x: 2001,
			y: 236,
			w: 250,
			h: 663,
		},
		{
			id: 'lens',
			name: 'Outer lens',
			material: 'PMMA, red-tinted, UV-stabilised',
			check: 'Red, within the chromaticity limits',
			x: 2287,
			y: 35,
			w: 465,
			h: 1033,
		},
	],
};
