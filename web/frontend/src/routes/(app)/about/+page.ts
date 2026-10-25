import { error } from '@sveltejs/kit';
import type { PageLoad } from './$types';

export const load: PageLoad = ({ url }) => {
	if (!url.searchParams.has('preview')) error(404, 'Not found');
};
