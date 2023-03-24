import type { Message } from '@bufbuild/protobuf';
import { MongoClient, ObjectId, Collection, FindCursor, type Filter, Binary } from 'mongodb';

const uri = 'mongodb+srv://cluster0.ndszdhz.mongodb.net/?authSource=$external';
const client = new MongoClient(uri, {
	tls: true,
	authMechanism: 'MONGODB-X509',
	tlsCertificateKeyFile: '../secrets/X509-cert-8051024250932727866.pem'
});

export const db = client.db('testdb');

export async function getOne<T extends Message>(
	coll: Collection,
	id: string | number,
	binaryId: boolean = true
): Promise<T> {
	const idFilter = makeIdFilter(id, binaryId);
	const resp = await coll.findOne(idFilter);
	return cleanDoc(resp);
}

export async function upsert(coll: Collection, msg: Message, binaryId: boolean = true) {
	if (!msg.id) {
		msg.id = new ObjectId().toHexString();
	}

	const json = msg.toJson()!;
	const id_filter = makeIdFilter(json.id, binaryId);
	delete json.id;

	return await coll.updateOne(id_filter, { $set: json }, { upsert: true });
}

export async function getEntitiesList(cursor: FindCursor): Promise<Array<any>> {
	const jsons = [];

	for await (let doc of cursor) {
		doc = cleanDoc(doc);
		jsons.push(doc);
	}

	return jsons;
}

export async function getEntitiesMap(cursor: FindCursor): Promise<Map<string, any>> {
	const map: Map<string, any> = new Map();

	for await (let doc of cursor) {
		doc = cleanDoc(doc);
		map.set(doc.id, doc);
	}

	return map;
}

function makeIdFilter(id: string, binaryId: boolean): any {
	return { _id: binaryId ? new ObjectId(id) : id };
}

function cleanDoc(doc: any): any {
	if (doc._id instanceof ObjectId) {
		doc.id = doc._id.toHexString();
	} else {
		doc.id = doc._id;
	}
	delete doc._id;

	if (doc.hash instanceof Binary) {
		doc.hash = btoa(doc.hash.value());
	}

	return doc;
}
