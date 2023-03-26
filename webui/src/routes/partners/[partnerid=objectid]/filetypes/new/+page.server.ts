import type { PageServerLoad } from './$types';

import { db, getOne } from '$lib/server/db';

import type { Partner } from '$lib/protos/config_pb';

export const load = (async ({ params, parent }) => {
	const partner: Promise<Partner> = getOne(db.collection('partners'), params.partnerid);

	return { partner: await partner };
}) satisfies PageServerLoad;
