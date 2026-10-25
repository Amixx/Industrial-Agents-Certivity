import { api } from '#lib/api/client.ts';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ params, url }) => {
	const run = url.searchParams.get('update');
	const [assessment, update] = await Promise.all([
		api.getAssessment(params.id),
		run ? api.getUpdate(params.id, run) : null,
	]);
	return { assessment, update };
};
