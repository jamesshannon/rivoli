import { json } from '@sveltejs/kit';

import { db } from '$lib/server/db';

import { File_Status } from '$lib/rivoli/protos/processing_pb';

import { createTask } from '$lib/helpers/celery';
import { makeLogMsg } from '$lib/helpers/utils';

export async function handleFilePostRequest(fileId: string, reqBody: any): any {
  if (reqBody.action == 'APPROVE_UPLOAD') {
    // this handles downgrading status to re-run uploads
    const log = makeLogMsg('Approved for uploading');

    // Update the file
    // Filter on the expected status (WAITING..) to prevent unexepcted states
    // and race conditions
    const resp = await db.collection('files').updateOne(
      { _id: parseInt(fileId), status: File_Status.WAITING_APPROVAL_TO_UPLOAD },
      {
        $set: { status: File_Status.APPROVED_TO_UPLOAD },
        $addToSet: { log: log.toJson({ enumAsInteger: true }) }
      }
    );

    if (resp.modifiedCount === 1) {
      // Now that the file status is updated, schedule the next step
      // Python code has the logic to schedule the next step so we use that
      // rather than try to recreate
      createTask('rivoli.status_scheduler', 'next_step_id', parseInt(fileId));

      return json({ status: 'success' });
    }
  } else if (reqBody.action === 'EXECUTE_REPORT') {
    const outputId = reqBody.outputId;

    createTask(
      'rivoli.reporter',
      'create_and_schedule_report_by_id',
      parseInt(fileId),
      outputId
    );

    return json({ status: 'success' });
  }

  return json({ status: 'error' });
}
