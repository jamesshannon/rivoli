import type { PageLoad } from './$types';

import { client } from '$lib/grpc';

export const load = (async ({ params }) => {
	const res = await client.getFunctionsBatch({});

	const functionsMap = new Map(res.functions.map((f) => [f.id, f]));

	return { functionsMap: functionsMap };
}) satisfies PageLoad;
