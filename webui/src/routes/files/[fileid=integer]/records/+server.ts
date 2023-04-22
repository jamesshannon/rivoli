import type { RequestHandler } from './$types';
import { json } from '@sveltejs/kit';

import { db, getEntitiesList, getEntitiesMap } from '$lib/server/db';

import {
  File_Status,
  ProcessingLog,
  ProcessingLog_LogLevel,
  Record_Status,
  type Record
} from '$lib/protos/processing_pb';
import type { URLSearchParams } from 'url';
import { time } from 'console';
import FileStatus from '$lib/components/FileStatus.svelte';

import { createTask } from '$lib/helpers/celery';

function makeBaseFilter(fileId: string): [any, any] {
  // Record ID portion is 1-based to correspond with file row numbers
  const baseRecordId = (BigInt(fileId) << 32n) + 1n;
  const maxRecordId = baseRecordId + ((1n << 32n) - 1n);

  const options: any = { sort: { _id: 1 } };
  const filter = { _id: { $gte: baseRecordId, $lte: maxRecordId } };
  return [filter, options];
}

function makeSearchFilter(fileId: string, params: any): [any, any] {
  const [filter, options] = makeBaseFilter(fileId);
  const startOffset = parseInt(params.start || '0');

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
  /*
    [
  {$match: {_id: {$gte: 73014444032,$lte: 77309411327}}},
  { $project: {_id: 0, status: 1, numRecentErrors: {$cond: {if: {$isArray: '$recentErrors'}, then: {$size: '$recentErrors'}, else: 0}}}},
  { $group: { _id: '$status', count: { $count: {} }, recentErrors: { $sum: '$numRecentErrors' } }}

  ]
  */

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

  return json({ records: await recordsP, statusCounts: statusCounts });
}

const revertStatusMap = new Map([
  [Record_Status.LOADED, File_Status.LOADED],
  [Record_Status.PARSED, File_Status.PARSED],
  [Record_Status.VALIDATED, File_Status.VALIDATED]
]);
const REVERTABLE_MAP = new Map([
  // copied from from page.svelte
  [Record_Status.PARSE_ERROR, [Record_Status.LOADED]],
  [
    Record_Status.VALIDATION_ERROR,
    [Record_Status.LOADED, Record_Status.PARSED]
  ],
  [
    Record_Status.UPLOAD_ERROR,
    [Record_Status.LOADED, Record_Status.PARSED, Record_Status.VALIDATED]
  ]
]);

export async function POST({ url, params, request }) {
  const reqBody = await request.json();

  if (reqBody.action == 'REVERT') {
    // this handles downgrading status to re-run uploads
    const fileId = params.fileid;
    const toRecordStatus = parseInt(reqBody.toStatus);
    const toRecordStatusName = Record_Status[toRecordStatus];

    const [filter, _] = makeSearchFilter(fileId, reqBody);

    console.log('filter', filter, toRecordStatus);
    if (!filter.status || !REVERTABLE_MAP.get(filter.status)) {
      // better error handling
      return json({ status: 'error1' });
    } else if (filter.status <= toRecordStatus) {
      return json({ status: 'error2' });
    }

    const toFileStatus = revertStatusMap.get(toRecordStatus);

    const log = new ProcessingLog({
      level: ProcessingLog_LogLevel.INFO,
      time: Math.floor(Date.now() / 1000),
      message: `Reverted status to ${toRecordStatusName}`
    });

    // update the records
    const update = {
      // Set the status to VALIDATED -- currently the only "to" status supported
      $set: { status: toRecordStatus },
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

    // Update the file
    const modified = resp.modifiedCount;
    log.message = `Reverted record status to ${toRecordStatusName} on ${modified} records`;
    db.collection('files').updateOne(
      { _id: parseInt(fileId) },
      {
        $set: { status: toFileStatus },
        $addToSet: { log: log.toJson({ enumAsInteger: true }) }
        // TODO: Update stats... and ss stats... :(
        // $inc: { 'stats.uploadedRecordsError': -1 * modified }
      }
    );

    // Now that the file status is updated, schedule the next step
    // Python code has the logic to schedule the next step so we use that
    // rather than try to recreate
    createTask('rivoli.status_scheduler', 'next_step_id', parseInt(fileId));
  }

  return json({ status: 'success' });
}
