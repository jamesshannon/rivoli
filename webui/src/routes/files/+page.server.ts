import type { PageServerLoad } from './$types';

import type { JsonValue } from '@bufbuild/protobuf';

import { db, getEntitiesList, getEntitiesMap } from '$lib/server/db';
import { Partner } from '$lib/rivoli/protos/config_pb';

export const load = (async ({ params, parent }) => {
  const filter = { isDevelopment: { $in: [null, false] } };
  let files = getEntitiesList(
    db.collection('files').find(filter).sort({ _id: -1 }).limit(100)
  );

  let partners: Map<string, Partner> = await getEntitiesMap(
    db.collection('partners').find()
  );
  console.log(partners, Array.from(partners.values()));

  let filetypes = new Map(
    Array.from(partners.values()).flatMap((p) =>
      Partner.fromJson(p as any as JsonValue).fileTypes.map((ft) => [
        ft.id,
        ft.toJson()
      ])
    )
  );

  return { partnerMap: partners, filetypeMap: filetypes, files: await files };
}) satisfies PageServerLoad;
