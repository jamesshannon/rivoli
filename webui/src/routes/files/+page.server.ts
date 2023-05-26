import type { PageServerLoad } from './$types';

import { db, getEntitiesList, getEntitiesMap } from '$lib/server/db';
import type { Partner } from '$lib/rivoli/protos/config_pb';
import type { File } from '$lib/rivoli/protos/processing_pb';

export const load = (async ({ params, parent }) => {
  const partners = getEntitiesList<Partner>(db.collection('partners').find());

  const filter = { isDevelopment: { $in: [null, false] } };
  const files = getEntitiesList<File>(
    db.collection('files').find(filter).sort({ _id: -1 }).limit(100)
  );

  return { partners: await partners, files: await files };
}) satisfies PageServerLoad;
