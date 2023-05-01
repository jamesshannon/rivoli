import { Record_Status } from '$lib/rivoli/protos/processing_pb';

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
