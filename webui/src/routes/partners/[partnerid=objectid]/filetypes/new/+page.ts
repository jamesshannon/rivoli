import type { PageLoad } from './$types';

import { client } from '$lib/grpc';

export const load = (async ({ params }) => {
	const res = await client.getPartner({ id: params.partnerid });
	return { partner: res.partner };
}) satisfies PageLoad;
