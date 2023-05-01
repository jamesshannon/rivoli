import {
  getRequestRecords,
  hanldePostRequestRevertRecords
} from '$lib/helpers/file_processing/server_apis/records';

export async function GET({ url, params }) {
  return await getRequestRecords(
    params.fileid,
    Object.fromEntries(url.searchParams)
  );
}

export async function POST({ params, request }) {
  const reqBody = await request.json();
  console.log('fileid or fileId', params);
  return await hanldePostRequestRevertRecords(params.fileid, reqBody);
}
