import type { PageServerLoad } from './$types';

import { db, getEntitiesMap } from '$lib/server/db';
import type { Partner } from '$lib/protos/config_pb';

export const load = (async ({ params, parent }) => {
	let partners: Map<string, Partner> = await getEntitiesMap(db.collection('partners').find());

	return { partners: partners };
}) satisfies PageServerLoad;
