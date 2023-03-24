import type { PageLoad } from './$types';

import { client } from '$lib/grpc';

export const load = (async ({ params }) => {
	const fileId = params.fileid;

	const partnersP = client.getPartnersBatch({});
	const file = (await client.getFile({ id: fileId })).file!;
	const partners = (await partnersP).partners;
	const partnermap = new Map(partners.map((p) => [p.id, p]));
	const filetypemap = new Map(partners.flatMap((p) => p.fileTypes.map((ft) => [ft.id, ft])));
	return {
		partner: partnermap.get(file.partnerId),
		filetype: filetypemap.get(file.fileTypeId),
		file: file
	};
}) satisfies PageLoad;
