export const prerender = false;

import type { LayoutLoad } from './$types';

export const load = (() => {
	return { layout: true };
}) satisfies LayoutLoad;
