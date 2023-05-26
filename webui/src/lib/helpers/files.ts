import {
  File_Status,
  type RecordStats
} from '$lib/rivoli/protos/processing_pb';

function loaded(stats: RecordStats) {
  return stats.loadedRecordsSuccess + stats.loadedRecordsError;
}

export const statuses = new Map([
  [
    File_Status.LOADING,
    {
      working: true,
    }
  ],
  [
    File_Status.PARSING,
    {
      working: true,
    }
  ],
  [
    File_Status.VALIDATING,
    {
      label: 'VALIDATING',
      working: true,
    }
  ],
  [
    File_Status.UPLOADING,
    {
      label: 'UPLOADING',
      working: true,
    }
  ]
]);
