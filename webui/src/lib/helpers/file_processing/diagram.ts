import type { File_Status, File } from '$lib/rivoli/protos/processing_pb';

export function getNodeStatus(
  file: File | undefined,
  processing: File_Status,
  error: File_Status,
  complete: File_Status
): string {
  if (!file) return '';

  if (file.status === processing) {
    return 'PROCESSING';
  } else if (file.status === error) {
    return 'ERROR';
  } else if (file.status >= complete) {
    return 'COMPLETE';
  }

  // Other statuses, which typically means "not yet processed"
  // But also some weird non-standard ones
  return '';
}
