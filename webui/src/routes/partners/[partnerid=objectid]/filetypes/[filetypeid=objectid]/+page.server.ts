import type { PageServerLoad } from './$types';

import { db, getOne, getEntitiesMap } from '$lib/server/db';

import type { Partner } from '$lib/protos/config_pb';
import type { Function } from '$lib/protos/functions_pb';

export const load = (async ({ params, parent }) => {
	const functions: Promise<Map<string, Function>> = getEntitiesMap(
		db.collection('functions').find()
	);
	const partner: Promise<Partner> = getOne(db.collection('partners'), params.partnerid);

	return { partner: await partner, functionsMap: await functions };
}) satisfies PageServerLoad;
