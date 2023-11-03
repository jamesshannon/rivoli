import { json } from '@sveltejs/kit';

import {
  handlePostApproveUpload,
  handlePostExecuteReport
} from '$lib/helpers/file_processing/server_apis/file';
import {
  getRequestRecords,
  handlePostRequestRevertRecords
} from '$lib/helpers/file_processing/server_apis/records';

export async function GET({ url, params }) {
  return await getRequestRecords(
    params.fileid,
    Object.fromEntries(url.searchParams)
  );
}

export async function POST({ params, request }) {
  const fileId = parseInt(params.fileid);
  const reqBody = await request.json();

  let responseP: Promise<any>;

  if (reqBody.action === 'REVERT_RECORDS') {
    responseP = handlePostRequestRevertRecords(fileId, reqBody);
  } else if (reqBody.action === 'APPROVE_UPLOAD') {
    responseP = handlePostApproveUpload(fileId, reqBody);
  } else if (reqBody.action === 'EXECUTE_REPORT') {
    responseP = handlePostExecuteReport(fileId, reqBody);
  } else {
    responseP = Promise.resolve({
      status: 'error',
      data: { message: 'Invalid request' }
    });
  }

  return json(await responseP);
}
