import type { PageServerLoad } from './$types';

import { jsonArray } from '$lib/helpers/utils';
import { db, getOne } from '$lib/server/db';

import type { FileType, Partner } from '$lib/rivoli/protos/config_pb';
import type { File } from '$lib/rivoli/protos/processing_pb';

function makeOutputFilter() {
  // take file & output
  // generate filter
  // function that starts with makeSearchFilter and then adds
  // additional filters on top.
  // * record status list ($in)
  // * failed function list
  // initially return the entire record
  // eventually we should filter out intermediary steps
  //{_id: {$gte: 219043330000}, recentErrors: {$elemMatch: {functionId: {$in: ["b921aea76104d6682dc2c636", "f829ef7b9e58b6d54b712e77"]}}}}
  // Note: Only support validation errors
}

export const load = (async ({ params }) => {
  const file = await getOne<File>(
    db.collection('files'),
    parseInt(params.fileid),
    false
  );
  const partner = await getOne<Partner>(
    db.collection('partners'),
    file.partnerId
  );
  const outputInst = file.outputs.find((o) => o.id == params.outputid)!;

  const output = jsonArray<FileType>(partner, 'fileTypes')
    .flatMap((ft) => ft.outputs)
    .find((o) => o.id === outputInst.outputId);

  return { file, partner, outputInst, output };
}) satisfies PageServerLoad;
