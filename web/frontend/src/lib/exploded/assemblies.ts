// The products the exploded view knows, and which one an assessment shows.

import type { Assessment } from '#lib/api/types.ts';
import { frontBumper } from './frontBumper.ts';
import { rearLamp } from './rearLamp.ts';
import type { ProductModel } from './scene3d.ts';

export interface ExplodedPart {
	id: string;
	name: string;
	material: string;
	check: string;
	facets: string[];
	x: number;
	y: number;
	w: number;
	h: number;
	cx?: number;
	/** Frame x of the part's centre once assembled; by default the parts stack around the middle. */
	home?: number;
}

export interface ExplodedAssembly {
	name: string;
	base: string;
	width: number;
	height: number;
	/** How the parts run from left to right in the scroll view, as in "rear to front". */
	order: string;
	/** The scroll view's first part is nearest the camera, so it draws on top. */
	firstOnTop?: boolean;
	/** What the light toggle in the 3D view switches, as in "Lamp on". */
	lights: string;
	/** The parametric model for the 3D view, loaded with three.js when that view opens. */
	model: () => Promise<ProductModel>;
	parts: ExplodedPart[];
}

export { frontBumper, rearLamp };

/** The assembly for an assessment's product, picked by case name or product type. */
export function assemblyFor(assessment: Assessment): ExplodedAssembly | null {
	const names = `${assessment.caseName ?? ''} ${assessment.profile.productType}`.toLowerCase();
	if (/\bbumper\b/.test(names) && !/\brear bumper\b/.test(names)) return frontBumper;
	if (/\b(rear|tail) (lamp|light)/.test(names)) return rearLamp;
	return null;
}
