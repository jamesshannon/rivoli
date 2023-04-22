import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';

import { db, getNextId, upsert } from '$lib/server/db';
import { Partner } from '$lib/protos/config_pb';

export const POST = (async ({ request }) => {
  const partner = Partner.fromJson(await request.json());

  // make manual updates

  // Create a new recordType.id if it's empty
  for (let ft of partner.fileTypes) {
    for (let rt of ft.recordTypes) {
      if (!rt.id) {
        rt.id = await getNextId('recordTypes', 1000);
      }
    }
  }

  const resp = upsert(db.collection('partners'), partner);

  return json({ partner: partner });
}) satisfies RequestHandler;

// async saveFunction(req) {
// 	try {
// 		const func = req.function!;
// 		if (!func.id) {
// 			func.id = new ObjectId().toHexString();
// 		}
// 		console.log("!!!!!", func);
// 		update(db.collection("functions"), func, false);
// 		return new SingleFunctionResponse({ function: func });
// 	} catch (err) {
// 		console.log(err);
// 	}
// },

// async getPartner(req) {
// 	const partner_id = req.id;

// 	const resp = await db
// 		.collection("partners")
// 		.findOne({ _id: new ObjectId(partner_id) });

// 	resp["id"] = resp["_id"].toHexString();

// 	for (let ft of resp.fileTypes) {
// 		for (let rt of ft.recordTypes) {
// 			for (ft of rt.fieldTypes) {
// 				convertOneOf(ft, "fieldLocation", [
// 					"charRange",
// 					"headerColumn",
// 					"columnIndex",
// 				]);
// 			}
// 		}
// 	}

// 	return new SinglePartnerResponse({ partner: resp });
// },

// async saveNewPartner(req) {
// 	const partner = req.partner!;

// 	try {
// 		const result = await db.collection("partners").insertOne(partner);
// 		partner.id = result.insertedId.toHexString();
// 	} catch (err) {
// 		console.log("got error", err);
// 	}

// 	return new SinglePartnerResponse({ partner: partner });
// },

// async savePartner(req) {
// 	const partner = req.partner!;
// 	console.log("saving partner", partner);

// 	for (const file of partner.fileTypes) {
// 		for (const record of file.recordTypes) {
// 			if (!record.id) {
// 				console.log("creating a new record id");
// 				record.id = await getNextId("recordTypes", 1000);
// 			}
// 		}
// 	}

// 	update(db.collection("partners"), partner);
// 	return new SinglePartnerResponse({ partner: req.partner! });
// },

// async function update(
//   coll: Collection,
//   msg: Message,
//   binaryId: boolean = true
// ) {
//   const json = msg.toJson()!;
//   const id_filter = { _id: binaryId ? new ObjectId(json.id) : json.id };
//   delete json.id;

//   try {
//     return await coll.updateOne(id_filter, { $set: json }, { upsert: true });
//   } catch (err) {
//     console.error("Caught error trying to update", err);
//     throw err;
//   }
// }
