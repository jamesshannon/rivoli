import { Record_Status } from '$lib/rivoli/protos/processing_pb';

interface SearchParams {
  start?: number | string;
  length?: number | string;
  status?: number | string;
  recentErrors?: string[];
}

// This map defines the record statuses which are revert-able, and the
// status(es) that those records can be reverted to.
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

  // The number of returned records for this particular filter.
  // This is "delayed" because it is set after the filter has been used to
  // retrieve filtered records.
  resultCount = 0;

  get filterObj(): { [key: string]: string } {
    return { status: this.status, errorCode: this.errorCode };
  }

  get statusSearchString(): string {
    return this.status == '0' ? '' : this.status;
  }

  reset() {
    this.status = '';
    this.errorCode = '';
  }
}

export function makeMongoRecordIdBaseFilter(
  fileId: string | number
): [any, any] {
  // Record ID portion is 1-based to correspond with file row numbers
  const baseRecordId = (BigInt(fileId) << 32n) + 1n;
  const maxRecordId = baseRecordId + ((1n << 32n) - 1n);

  const filter = { _id: { $gte: baseRecordId, $lte: maxRecordId } };
  const options: any = { sort: { _id: 1 } };
  return [filter, options];
}

export function makeMongoRecordSearchFilter(
  fileId: string | number,
  params: SearchParams
): [any, any] {
  const [filter, options] = makeMongoRecordIdBaseFilter(fileId);

  // Offset (paging)
  // If there are no filters then the offset can be done with math (using the
  // recordId), but the existence of any filters requires setting the `skip`
  // option and having Mongo iterate through all the records
  const startOffset = Number(params.start) || 0;
  options.limit = Number(params.length) || 10;

  if (params.status) {
    filter.status = Number(params.status);
    //filter.status = { $in: params.status };
    options.skip = startOffset;
  }

  if (params.recentErrors) {
    filter.recentErrors = {
      $elemMatch: { functionId: { $in: params.recentErrors } }
    };
    options.skip = startOffset;
  }

  if (options.skip === undefined) {
    filter._id.$gte = filter._id.$gte + BigInt(startOffset);
  }

  return [filter, options];
}
