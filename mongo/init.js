// We only care about the hashes, and we only care about the hashes which are
// not null, but we cannot exclude _id in the index, partialFilterExpression
// cannot be used with sparse, and cannot filter on $ne: null, so this will
// have to do.
db.records.createIndex(
  {
    "hash": 1
  },
  {
    partialFilterExpression: {
      hash: { $exists: true },
      status: { $gte: 80 },
    },
  }
);
