import type { RequestHandler } from './$types';
import { json } from '@sveltejs/kit';

import { db, getEntitiesList, getEntitiesMap } from '$lib/server/db';

import type { Record } from '$lib/protos/processing_pb';

export async function GET({ url, params }) {
  let status_filter = url.searchParams.get('status_filter') || '';

  const startOffset = parseInt(url.searchParams.get('start') || '0');
  const limit = parseInt(url.searchParams.get('length') || '10');

  const baseRecordId = BigInt(params.fileid) << 32n;
  const maxRecordId = baseRecordId + ((1n << 32n) - 1n);

  const filter: any = { _id: { $gte: baseRecordId, $lte: maxRecordId } };
  const options: any = { sort: { _id: 1 } };

  // Begin the aggregation counting with the "base" filter
  const countCursor = db
    .collection('records')
    .aggregate([
      { $match: { ...filter } },
      { $group: { _id: '$status', count: { $count: {} } } }
    ]);

  if (status_filter) {
    // Can no longer use the ID-based filter as an offset
    filter.status = parseInt(status_filter);
    options.skip = startOffset;
  } else {
    filter._id.$gte = baseRecordId + BigInt(startOffset);
  }

  console.log(filter, options);

  const recordsCursor = db
    .collection('records')
    .find(filter, options)
    .limit(limit);

  console.log(filter, options);

  const countP = getEntitiesList(countCursor);
  const recordsP = getEntitiesList<Record>(recordsCursor);

  const statusCounts: Map<number, number> = Object.fromEntries(
    (await countP).map((s) => [s.id, s.count])
  );

  return json({ records: await recordsP, statusCounts: statusCounts });
}
