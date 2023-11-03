import { json } from '@sveltejs/kit';

import {
  getRequestRecords
} from '$lib/helpers/file_processing/server_apis/records';

export async function GET({ url, params }) {
  console.log(params);
  return await getRequestRecords(
    params.fileid,
    Object.fromEntries(url.searchParams)
  );
}
