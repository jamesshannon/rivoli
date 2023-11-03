import { db } from '$lib/server/db';

import { File_Status } from '$lib/rivoli/protos/processing_pb';

import { createTask } from '$lib/helpers/celery';
import { makeLogMsg } from '$lib/helpers/utils';

export async function handlePostApproveUpload(fileId: number, reqBody: any
    ): Promise<{ [key: string]: any }> {
  // this handles downgrading status to re-run uploads
  const log = makeLogMsg('Approved for uploading');

  // Update the file
  // Filter on the expected status (WAITING..) to prevent unexpected states
  // and race conditions
  const resp = await db.collection('files').updateOne(
    { _id: fileId, status: File_Status.WAITING_APPROVAL_TO_UPLOAD },
    {
      $set: { status: File_Status.APPROVED_TO_UPLOAD },
      $addToSet: { log: log.toJson({ enumAsInteger: true }) }
    }
  );

  if (resp.modifiedCount === 1) {
    // Now that the file status is updated, schedule the next step
    // Python code has the logic to schedule the next step so we use that
    // rather than try to recreate

    const kwargs = reqBody.limit ? {limit: reqBody.limit} : undefined;
    createTask('rivoli.status_scheduler', 'next_step_id', [fileId], kwargs);

    return {
      status: 'success',
      data: { message: 'Upload approved. Scheduled uploading.' }
    };
  }

  return {
      status: 'error',
      data: { message: 'Something went wrong approving the upload.' }
  };
}

export async function handlePostExecuteReport(fileId: number, reqBody: any
    ): Promise<{ [key: string]: any }> {
  const outputId = reqBody.outputId;

  createTask(
    'rivoli.reporter',
    'create_and_schedule_report_by_id',
    [fileId, outputId]
  );

  return {
    status: 'success',
    data: { message: 'Report scheduled for execution.' }
  };
}
