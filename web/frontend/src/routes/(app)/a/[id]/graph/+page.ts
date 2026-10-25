import { api } from '#lib/api/client.ts';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ params }) => ({
	assessment: await api.getAssessment(params.id),
});
