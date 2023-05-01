import { handleFilePostRequest } from '$lib/helpers/file_processing/server_apis/file';

export async function POST({ params, request }) {
  return await handleFilePostRequest(params.fileid, await request.json());
}
