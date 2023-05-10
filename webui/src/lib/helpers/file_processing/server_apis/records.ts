import { json } from '@sveltejs/kit';

import { createTask } from '$lib/helpers/celery';
import { makeLogMsg } from '$lib/helpers/utils';
import { db, getEntitiesList } from '$lib/server/db';

import {
  File_Status,
  type Record,
  Record_Status
} from '$lib/rivoli/protos/processing_pb';
import { REVERTABLE_MAP } from '$lib/helpers/file_processing/records';

// Map Record status to File Status to determine which status to set
// the File to if the Records are reverted to "X"
const revertStatusMap = new Map([
  [Record_Status.LOADED, File_Status.LOADED],
  [Record_Status.PARSED, File_Status.PARSED],
  [Record_Status.VALIDATED, File_Status.VALIDATED]
]);

function makeBaseFilter(fileId: string | number): [any, any] {
  // Record ID portion is 1-based to correspond with file row numbers
  const baseRecordId = (BigInt(fileId) << 32n) + 1n;
  const maxRecordId = baseRecordId + ((1n << 32n) - 1n);

  const options: any = { sort: { _id: 1 } };
  const filter = { _id: { $gte: baseRecordId, $lte: maxRecordId } };
  return [filter, options];
}

function makeSearchFilter(fileId: string | number, params: any): [any, any] {
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

export async function getRequestRecords(
  fileId: string,
  reqParams: { [k: string]: string }
) {
  const limit = parseInt(reqParams.length || '10');

  // Begin the aggregation counting with the "base" filter
  const countCursor = db
    .collection('records')
    .aggregate([
      { $match: makeBaseFilter(fileId)[0] },
      { $group: { _id: '$status', count: { $count: {} } } }
    ]);

  const [filter, options] = makeSearchFilter(fileId, reqParams);

  // Begin the scan for the batch of records
  const recordsCursor = db
    .collection('records')
    .find(filter, options)
    .limit(limit);

  const countP = getEntitiesList(countCursor);
  const recordsP = getEntitiesList<Record>(recordsCursor);

  const statusCounts: Map<string, number> = Object.fromEntries(
    (await countP).map((s) => [s.id, s.count])
  );

  return json({ records: await recordsP, statusCounts: statusCounts });
}

export async function handlePostRequestRevertRecords(
  fileId: number,
  reqBody: any
): Promise<{ [key: string]: string }> {
  // this handles downgrading status to re-run uploads
  const toRecordStatus = parseInt(reqBody.toStatus);
  const toRecordStatusName = Record_Status[toRecordStatus];

  const [filter, _] = makeSearchFilter(fileId, reqBody);

  if (!filter.status || !REVERTABLE_MAP.get(filter.status)) {
    // better error handling
    return { status: 'error1' };
  } else if (filter.status <= toRecordStatus) {
    return { status: 'error2' };
  }

  const toFileStatus = revertStatusMap.get(toRecordStatus);
  const log = makeLogMsg(`Reverted status to ${toRecordStatusName}`);

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
    { _id: fileId },
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
  createTask('rivoli.status_scheduler', 'next_step_id', fileId);

  return { status: 'success' };
}
