import type { PageServerLoad } from './$types';

import { db, getEntitiesList } from '$lib/server/db';
import type { Function } from '$lib/protos/functions_pb';

export const load = (async () => {
	const functions = await getEntitiesList<Function>(db.collection('functions').find());

	return { functions: functions };
}) satisfies PageServerLoad;
