import { env } from '$env/dynamic/private';

import type { Message } from '@bufbuild/protobuf';
import {
  MongoClient,
  ObjectId,
  Collection,
  AbstractCursor,
  type Filter,
  Binary
} from 'mongodb';

let client: MongoClient;

if (!env.mongo_authkey) {
  const auth = `${env.MONGO_USERNAME}:${env.MONGO_PASSWORD}`;
  const uri = `mongodb://${auth}@${env.MONGO_ENDPOINT}`;
  client = new MongoClient(uri);
} else {
  client = new MongoClient('xxxx');
}

export const db = client.db(env.MONGO_DB);

export async function getNextId(
  collection: string,
  offset: number = 0
): Promise<number> {
  const resp = await db
    .collection('counters')
    .findOneAndUpdate(
      { _id: collection },
      { $inc: { value: 1 } },
      { upsert: true, returnDocument: 'after' }
    );
  return parseFloat(resp.value!.value) + offset;
}

export async function getOne<T extends Message>(
  coll: Collection,
  id: string | number,
  binaryId: boolean = true
): Promise<T> {
  const idFilter = makeIdFilter(id, binaryId);
  const resp = await coll.findOne(idFilter);
  return cleanDoc(resp);
}

export async function upsert(
  coll: Collection,
  msg: Message,
  binaryId: boolean = true
) {
  if (!msg.id) {
    msg.id = new ObjectId().toHexString();
  }

  const json = msg.toJson({ enumAsInteger: true })!;
  const id_filter = makeIdFilter(json.id, binaryId);
  delete json.id;

  return await coll.updateOne(id_filter, { $set: json }, { upsert: true });
}

export async function getEntitiesList<T extends Message>(
  cursor: AbstractCursor
): Promise<Array<T>> {
  const docs = [];

  for await (let doc of cursor) {
    doc = cleanDoc(doc);
    docs.push(doc);
  }

  return docs;
}

export async function getEntitiesMap<T extends Message>(
  cursor: AbstractCursor
): Promise<Map<string, T>> {
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
