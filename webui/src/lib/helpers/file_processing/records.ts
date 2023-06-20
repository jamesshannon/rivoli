import { Record_Status } from '$lib/rivoli/protos/processing_pb';

interface SearchParams {
  start?: number | string;
  length?: number | string;
  status?: number | string;
  text?: string;
  recentErrors?: string[];
}

// This map defines the record statuses which are revert-able, and the
// status(es) to which those records can be reverted.
// Allow reverting of record statuses when only one status is filtered and
// that status is a PARSE_ERROR, VALIDATION_ERROR, or UPLOAD_ERROR
export const REVERTABLE_MAP = new Map([
  [Record_Status.PARSE_ERROR, [Record_Status.LOADED]],
  [
    Record_Status.VALIDATION_ERROR,
    [Record_Status.LOADED, Record_Status.PARSED]
  ],
  [
    Record_Status.UPLOAD_ERROR,
    [Record_Status.LOADED, Record_Status.PARSED, Record_Status.VALIDATED]
  ]
]);

export class RecordsFilter {
  status: string = '';
  errorCode: string = '';
  text: string = '';

  // The number of returned records for this particular filter.
  // This is "delayed" because it is set after the filter has been used to
  // retrieve filtered records.
  resultCount = 0;

  get filterObj(): { [key: string]: string } {
    return {
      status: this.status,
      errorCode: this.errorCode,
      text: this.text
    };
  }

  get statusSearchString(): string {
    return this.status == '0' ? '' : this.status;
  }

  reset() {
    this.status = '';
    this.errorCode = '';
    this.text = '';
  }
}

function escapeRegex(str: string) {
  return str.replace(/[/\-\\^$*+?.()|[\]{}]/g, '\\$&');
}

function recordIds(fileId: string | number): [bigint, bigint] {
  // Record ID is 1-based to correspond with file row numbers
  const startId = (BigInt(fileId) << 32n) + 1n;
  return [startId, startId + ((1n << 32n) - 1n)];
}

export function makeRecordFilterPipeline(fileId: string | number,
    params: SearchParams, aggStatuses = false): {[key: string]: any}[] {
  const stages = [];

  let [startRecordId, maxRecordId] = recordIds(fileId);

  // Skipping is based on whether or not filters are applied
  let isFiltered = false;

  // Mongodb optimizes multiple $match stages into a single stage so all $match
  // stages should be done at the same time, and they should be done as early
  // as possible.
  // The most fundamental $match filter is the record id range, but the details
  // of that will depend on whether filters are applied, so the record id $match
  // is created at the end but will be prepended to the stages array.

  // Status filter
  if (params.status && ! aggStatuses) {
    isFiltered = true;
    stages.push({ $match: { status: Number(params.status) } });
  }

  // Recent Errors filters for the function ID(s) of any recent error
  if (params.recentErrors) {
    isFiltered = true;

    stages.push({ $match: { recentErrors:
      { $elemMatch: { functionId: { $in: params.recentErrors } } } } });
  }

  // Text filter is a partial string match for any field value or recent error
  // message. Matching on arbitrary field values requires converting the field
  // object to an array in one stage and then matching in a later stage.
  if (params.text) {
    isFiltered = true;
    // Partial string case-insensitive match
    const filter = { $regex: escapeRegex(params.text), $options: 'i' };

    stages.push({ $set: {
      parsedFieldArray: { $objectToArray: "$parsedFields" },
      validatedFieldArray: { $objectToArray: "$validatedFields" }
    }});
    stages.push({ $match: { $or: [
      { 'parsedFieldArray.v': filter },
      { 'validatedFieldArray.v': filter },
      { 'recentErrors': { $elemMatch: { message: filter } } },
    ]}});
  }

  // Sort the records by the Record ID (which is also row order)
  // This doesn't affect the status aggregation query; it's not necessary, but
  // appears to get optimized out.
  stages.push({ $sort: { _id: 1 } });

  // Record ID Filtering & Skipping
  const startOffset = Number(params.start) || 0;
  if (aggStatuses) {
    // Aggregating Status Counts -- don't "skip" at all
  } else if (! isFiltered) {
    // Simple Case -- no filtering has happened so we can skip with math
    startRecordId = startRecordId + BigInt(startOffset);
  } else if (startOffset > 0) {
    // If we're filtering then we need to skip with a $skip stage after the
    // $match stage(s).
    stages.push({ $skip: startOffset });
  }

  // Add the record ID $match stage to the very beginning.
  stages.unshift(
      { $match: { _id: { $gte: startRecordId, $lte: maxRecordId } } });

  // Add the limit stage to the end if we're not aggregating the statuses
  if (! aggStatuses) {
    stages.push({ $limit: Number(params.length) || 10 });
  }

  return stages;
}

export function makeRecordStatusFilter(fileId: string | number,
    statusId: number): {[key: string]: any} {
  // A status filter is a filter (not an aggregation pipeline) which only
  // filters for a particular file (based on record ID) and the Status ID
  const [startRecordId, maxRecordId] = recordIds(fileId);

  return {
    _id: { $gte: startRecordId, $lte: maxRecordId },
    status: statusId
  };
}
