import type { RequestHandler } from './$types';
import { json } from '@sveltejs/kit';

import { db, getEntitiesList, getEntitiesMap } from '$lib/server/db';

import {
  ProcessingLog,
  ProcessingLog_LogLevel,
  Record_Status,
  type Record
} from '$lib/protos/processing_pb';
import type { URLSearchParams } from 'url';
import { time } from 'console';

function makeBaseFilter(fileId: string): [any, any] {
  const baseRecordId = BigInt(fileId) << 32n;
  const maxRecordId = baseRecordId + ((1n << 32n) - 1n);

  const options: any = { sort: { _id: 1 } };
  const filter = { _id: { $gte: baseRecordId, $lte: maxRecordId } };
  return [filter, options];
}

function makeSearchFilter(fileId: string, params: any): [any, any] {
  const [filter, options] = makeBaseFilter(fileId);
  const startOffset = parseInt(params.start || '0');

  console.log(params);
  if (params.status) {
    // With active filters any skipping must be done by iterating through the
    // records
    filter.status = parseInt(params.status);
    options.skip = startOffset;
  } else {
    // Without any filters we can skip with math!
    filter._id.$gte = filter._id.$gte + BigInt(startOffset);
  }

  return [filter, options];
}

export async function GET({ url, params }) {
  const fileId: string = params.fileid;
  const reqParams = Object.fromEntries(url.searchParams);
  const limit = parseInt(reqParams.length || '10');

  // Begin the aggregation counting with the "base" filter
  const countCursor = db
    .collection('records')
    .aggregate([
      { $match: makeBaseFilter(fileId)[0] },
      { $group: { _id: '$status', count: { $count: {} } } }
    ]);

  const [filter, options] = makeSearchFilter(fileId, reqParams);

  const recordsCursor = db
    .collection('records')
    .find(filter, options)
    .limit(limit);

  console.log(filter, options);

  const countP = getEntitiesList(countCursor);
  const recordsP = getEntitiesList<Record>(recordsCursor);

  const statusCounts: Map<string, number> = Object.fromEntries(
    (await countP).map((s) => [s.id, s.count])
  );
  console.log(statusCounts);

  return json({ records: await recordsP, statusCounts: statusCounts });
}

export async function POST({ url, params, request }) {
  const reqBody = await request.json();

  // this handles downgrading status to re-run uploads
  const fileId = params.fileid;
  const [filter, _] = makeSearchFilter(fileId, reqBody);

  console.log('filter', filter);
  if (!filter.status || filter.status != 70) {
    // better error handling
    return json({ status: 'error' });
  }

  const log = new ProcessingLog({
    level: ProcessingLog_LogLevel.INFO,
    time: Math.floor(Date.now() / 1000),
    message: 'Reverted status to VALIDATED to retry'
  });

  // update the records
  const update = {
    // Set the status to VALIDATED -- currently the only "to" status supported
    $set: { status: Record_Status.VALIDATED.valueOf() },
    // Remove the log of recentErrors
    $unset: { recentErrors: {}, autoRetry: {} },
    // Add a log entry describing this reverting
    $addToSet: {
      log: log.toJson({ enumAsInteger: true }) as any
    },
    // Increment the retry count
    $inc: { retryCount: 1 }
  };

  const resp = await db.collection('records').updateMany(filter, update);
  console.log(resp);

  // Update the file
  const modified = resp.modifiedCount;
  log.message = `Reverted record status to VALIDATED on ${modified} records`;
  db.collection('files').updateOne(
    { _id: parseInt(fileId) },
    {
      $addToSet: { log: log.toJson({ enumAsInteger: true }) },
      $inc: { 'stats.uploadedRecordsError': -1 * modified }
    }
  );

  return json({ status: 'success' });
}
