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

export async function POST({ url, params, request }) {
  const reqBody = await request.json();

  if (reqBody.action == 'APPROVE_UPLOAD') {
    // this handles downgrading status to re-run uploads
    const fileId = params.fileid;

    const log = new ProcessingLog({
      level: ProcessingLog_LogLevel.INFO,
      time: Math.floor(Date.now() / 1000),
      message: `Approved for uploading`
    });

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
  }

  return json({ status: 'error' });
}
