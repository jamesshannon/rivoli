import { File_Status, type RecordStats } from '$lib/protos/processing_pb';

function loaded(stats: RecordStats) {
  return stats.loadedRecordsSuccess + stats.loadedRecordsError;
}

export const statuses = new Map([
  [
    File_Status.LOADING,
    {
      working: true,
      loading_pct: (s: RecordStats) => loaded(s) / s.approximateRows
    }
  ],
  [
    File_Status.PARSING,
    {
      working: true,
      loading_pct: (s: RecordStats) =>
        (s.parsedRecordsSuccess + s.parsedRecordsError) /
        (s.loadedRecordsSuccess + s.loadedRecordsError),
      success_pct: (s: RecordStats) => s.parsedRecordsSuccess / loaded(s)
    }
  ],
  [
    File_Status.VALIDATING,
    {
      label: 'VALIDATING',
      working: true,
      loading_pct: (s: RecordStats) =>
        (s.validatedRecordsSuccess + s.validatedRecordsError) /
        (s.parsedRecordsSuccess + s.parsedRecordsError),
      success_pct: (s: RecordStats) => s.validatedRecordsSuccess / loaded(s)
    }
  ]
]);
