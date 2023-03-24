import type { PageLoad } from './$types';

import { client } from '$lib/grpc';

export const load = (async ({ params }) => {
	const res = await client.getFunctionsBatch({});
	const func = new Map(res.functions.map((f) => [f.id, f])).get(params.functionid);

	return { func: func };
}) satisfies PageLoad;
