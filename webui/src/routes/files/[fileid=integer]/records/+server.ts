import type { RequestHandler } from './$types';
import { json } from '@sveltejs/kit';

import { db, getEntitiesList } from '$lib/server/db';

import type { Record } from '$lib/protos/processing_pb';

export async function GET({ url, params }) {
	const baseRecordId = BigInt(params.fileid) << 32n;
	const minRecordId = baseRecordId + BigInt(url.searchParams.get('start') || 0);
	const maxRecordId = baseRecordId + ((1n << 32n) - 1n);
	const limit = parseInt(url.searchParams.get('length') || '10');
	const filter = { _id: { $gte: minRecordId, $lte: maxRecordId } };

	const recordsP = getEntitiesList<Record>(
		db.collection('records').find(filter).sort({ _id: 1 }).limit(limit)
	);

	return json(await recordsP);
}
