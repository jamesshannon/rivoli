import type { PageServerLoad } from './$types';

import { db, getEntitiesList, getOne } from '$lib/server/db';

import type { Partner } from '$lib/protos/config_pb';
import { Record, type File } from '$lib/protos/processing_pb';

function jsonArray(obj: any, field: string): Array<any> {
	return obj[field] ? obj[field] : Array();
}

export const load = (async ({ params }) => {
	const file = await getOne<File>(db.collection('files'), parseInt(params.fileid), false);
	const partner = await getOne<Partner>(db.collection('partners'), file.partnerId);
	const fileType = jsonArray(partner, 'fileTypes').find((ft) => ft.id === file.fileTypeId);

	return { file: file, partner: partner, fileType: fileType };
}) satisfies PageServerLoad;