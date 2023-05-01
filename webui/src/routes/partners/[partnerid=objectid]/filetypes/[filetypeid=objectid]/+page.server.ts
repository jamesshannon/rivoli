import type { PageServerLoad } from './$types';

import { db, getOne, getEntitiesList } from '$lib/server/db';

import type { Partner } from '$lib/rivoli/protos/config_pb';
import type { Function } from '$lib/rivoli/protos/functions_pb';

export const load = (async ({ params, parent }) => {
  const functions = getEntitiesList<Function>(
    db.collection('functions').find()
  );
  const partner = getOne<Partner>(db.collection('partners'), params.partnerid);

  return { partner: await partner, functions: await functions };
}) satisfies PageServerLoad;
