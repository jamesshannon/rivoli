<script lang="ts">
  import { ProgressIndicator, ProgressStep } from 'carbon-components-svelte';

  import { dateTime, fmtNum } from '$lib/helpers/utils';
  import { File_Status, File } from '$lib/rivoli/protos/processing_pb';

  export let file: File;

  // Maps File statuses to the "current" index on the progress bar.
  // Only the 'ing' statuses get a "current" designator
  const currentIndexMap = new Map([
    [File_Status.LOADING, 1],
    [File_Status.PARSING, 2],
    [File_Status.VALIDATING, 3],
    [File_Status.UPLOADING, 4]
  ]);

  let currentIndex: number;
  // Set currentIndex default really high, otherwise the first step is current
  $: currentIndex = currentIndexMap.get(file.status) || 20;
</script>

<div class="progress_bar">
  <ProgressIndicator vertical preventChangeOnClick {currentIndex}>
    <ProgressStep complete description="Find file and add to database">
      <h5>Create File</h5>
      {dateTime(file.created)}<br />
      {#if file.stats?.approximateRows}
        File Lines: {fmtNum(file.stats?.approximateRows)}<br />
      {/if}
    </ProgressStep>
    <ProgressStep
      invalid={file.status == File_Status.LOAD_ERROR}
      complete={file.status >= File_Status.LOADING}
      description="Read file, detect record type(s), and load individual records into database"
    >
      <h5>Load Records</h5>
      {#if file.status >= File_Status.LOADING}
        {dateTime(file.times?.loadingStartTime)}<br />
        Successful Records: {fmtNum(file.stats?.loadedRecordsSuccess)}<br />
        Failed Records: {fmtNum(file.stats?.loadedRecordsError)}<br />
      {/if}
    </ProgressStep>
    <ProgressStep
      invalid={file.status == File_Status.PARSE_ERROR}
      complete={file.status >= File_Status.PARSING}
      description="Parse fields from loaded records based on record format"
    >
      <h5>Parse Records</h5>
      {#if file.status >= File_Status.PARSING}
        {dateTime(file.times?.parsingStartTime)}<br />
        Successful Records: {fmtNum(file.stats?.parsedRecordsSuccess)}<br />
        Failed Records: {fmtNum(file.stats?.parsedRecordsError)}<br />
      {/if}
    </ProgressStep>
    <ProgressStep
      invalid={file.status == File_Status.VALIDATE_ERROR}
      complete={file.status >= File_Status.VALIDATING}
      description="Validate individual fields and entire records"
    >
      <h5>Validate Records</h5>
      {#if file.status >= File_Status.VALIDATING}
        {dateTime(file.times?.validatingStartTime)}<br />
        Successful Records: {fmtNum(file.stats?.validatedRecordsSuccess)}<br />
        Failed Records: {fmtNum(file.stats?.validatedRecordsError)}<br />
        Total Validation Errors: {fmtNum(
          (file.stats?.validationErrors || 0) +
            (file.stats?.validationExecutionErrors || 0)
        )}
      {/if}
    </ProgressStep>
    <ProgressStep
      invalid={file.status == File_Status.UPLOAD_ERROR}
      complete={file.status >= File_Status.UPLOADING}
      description="Upload records to final destination"
    >
      <h5>Upload Records</h5>
      {#if file.status >= File_Status.UPLOADING}
        {dateTime(file.times?.uploadingStartTime)}<br />
        Successful Records: {fmtNum(file.stats?.uploadedRecordsSuccess)}<br />
        Failed Records: {fmtNum(file.stats?.uploadedRecordsError)}<br />
      {/if}
    </ProgressStep>
  </ProgressIndicator>
</div>

<style>
  .progress_bar {
    min-width: 230px;
  }

  .progress_bar :global(.bx--progress-step-button) {
    min-height: 2.5rem;
    padding-bottom: 0.75rem;
  }

  .progress_bar h5 {
    font-weight: 500;
    margin-top: -2px;
  }

  .progress_bar :global(li.bx--progress-step--current svg) {
    animation: spin 5s linear infinite;
  }

  @keyframes spin {
    70% {
      transform: rotate(360deg);
    }
    100% {
      transform: rotate(360deg);
    }
  }
</style>
