import type { PageServerLoad } from './$types';

import { db, getOne } from '$lib/server/db';
import type { Function } from '$lib/rivoli/protos/functions_pb';

export const load = (async ({ params }) => {
  const func = await getOne<Function>(
    db.collection('functions'),
    params.functionid,
    false
  );

  return { func: func };
}) satisfies PageServerLoad;
