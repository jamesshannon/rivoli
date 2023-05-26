import { json } from '@sveltejs/kit';

import {
  handlePostApproveUpload,
  handlePostExecuteReport
} from '$lib/helpers/file_processing/server_apis/file';
import {
  getRequestRecords,
  handleGetRequestOutputRecords,
  handlePostRequestRevertRecords
} from '$lib/helpers/file_processing/server_apis/records';

export async function GET({ url, params }) {
  console.log(params);
  return await handleGetRequestOutputRecords(
    params.fileid,
    Object.fromEntries(url.searchParams)
  );
}
