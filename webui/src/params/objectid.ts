import type { ParamMatcher } from '@sveltejs/kit';

export const match = ((param) => {
	return /^[a-fA-F0-9]{24}$/.test(param);
}) satisfies ParamMatcher;
