export const prerender = true;

import type { LayoutLoad } from './$types';

export const load = (() => {
	return { layout: true };
}) satisfies LayoutLoad;
