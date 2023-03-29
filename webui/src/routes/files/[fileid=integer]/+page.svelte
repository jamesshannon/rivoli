<script lang="ts">
  import 'carbon-components-svelte/css/g10.css';

  import {
    Button,
    Breadcrumb,
    BreadcrumbItem,
    Grid,
    Row,
    Column,
    ProgressIndicator,
    ProgressStep,
    Tag
  } from 'carbon-components-svelte';

  import type { PageData } from './$types';
  import { invalidateAll } from '$app/navigation';

  import FileStatus from '$lib/components/FileStatus.svelte';
  import ProcessingLogsTable from '$lib/components/ProcessingLogsTable.svelte';

  import { dateTime } from '$lib/helpers/utils';
  import { statuses } from '$lib/helpers/files';
  import { onMount } from 'svelte';

  import { type Partner, FileType } from '$lib/protos/config_pb';
  import { File_Status, File } from '$lib/protos/processing_pb';

  export let data: PageData;
  let file: File;
  const filetype = FileType.fromJson(data.fileType as any as JsonValue);
  function setFileFromData() {
    file = File.fromJson(data.file as any as JsonValue);
  }
  async function refreshFileData() {
    // invalidate($page.url) does not work, so we invalidate everything
    await invalidateAll();
    setFileFromData();
  }
  setFileFromData();

  onMount(() => {
    refreshFile();
  });

  function refreshFile() {
    const refresh_time = statuses.get(file.status)?.working ? 30_000 : 120_000;
    setTimeout(() => {
      refreshFileData();
      refreshFile();
    }, refresh_time);
  }

  function bufferToHex(buffer) {
    return [...new Uint8Array(buffer)]
      .map((b) => b.toString(16).padStart(2, '0'))
      .join('');
  }

  function fmtNum(num: number | BigInt | undefined) {
    return num ? num.toLocaleString() : 0;
  }

  // Maps File statuses to the "current" index on the progress bar.
  // Only the 'ing' statuses get a "current" designator
  const currentIndexMap = new Map([
    [File_Status.LOADING, 1],
    [File_Status.PARSING, 2],
    [File_Status.VALIDATING, 3],
    [File_Status.UPLOADING, 4]
  ]);

  let currentIndex: number;
  // Set currentIndex really high, otherwise the first step is current
  $: currentIndex = currentIndexMap.get(file.status) || 20;

  import { invalidate } from '$app/navigation';
</script>

<Breadcrumb noTrailingSlash>
  <BreadcrumbItem href="/">Home</BreadcrumbItem>
  <BreadcrumbItem href="/files">File Processing</BreadcrumbItem>
  <BreadcrumbItem href="/files/{file.id}" isCurrentPage
    >{file.name}</BreadcrumbItem
  >
</Breadcrumb>

<br /><br />
<h4>
  <a href="/partners/{file.partnerId}">{data.partner?.name}</a> -
  <a href="/partners/{file.partnerId}/filetypes/{file.fileTypeId}"
    >{data.fileType?.name}</a
  >
</h4>
<h2>
  {file.name} <span class="id">(File ID: {file.id})</span>
  {#if file.isDevelopment}<Tag>Development File</Tag>{/if}
</h2>
<!-- <FileStatus {file} /> -->

<div class="file_details">
  <div class="progress_bar">
    <ProgressIndicator vertical preventChangeOnClick {currentIndex}>
      <ProgressStep complete description="Find file and add to database">
        <h5>Create File</h5>
        {dateTime(file.created)}<br />
        {#if file.stats?.approximateRows}
          Approximate Rows: {fmtNum(file.stats?.approximateRows)}<br />
        {/if}
      </ProgressStep>
      <ProgressStep
        complete={file.status >= File_Status.LOADING}
        description="Read file, detect record type(s), and load individual records into database"
      >
        <h5>Load Records</h5>
        {#if file.status >= File_Status.LOADING}
          {dateTime(file.times.loadingStartTime)}<br />
          Successful Records: {fmtNum(file.stats?.loadedRecordsSuccess)}<br />
          Failed Records: {fmtNum(file.stats?.loadedRecordsError)}<br />
        {/if}
      </ProgressStep>
      <ProgressStep
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
        complete={file.status >= File_Status.VALIDATING}
        description="Validate individual fields and entire records"
      >
        <h5>Validate Records</h5>
        {#if file.status >= File_Status.VALIDATING}
          {dateTime(file.times?.validatingStartTime)}<br />
          Successful Records: {fmtNum(file.stats?.validatedRecordsSuccess)}<br
          />
          Failed Records: {fmtNum(file.stats?.validatedRecordsError)}<br />
          Total Validation Errors: {fmtNum(
            (file.stats?.validationErrors || 0) +
              (file.stats?.validationExecutionErrors || 0)
          )}
        {/if}
      </ProgressStep>
      <ProgressStep
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

  <Grid>
    <Row>
      <Column>
        <h5>Size</h5>
        {fmtNum(file.sizeBytes / 1000n)} KB
      </Column>
      <Column>
        <h5>MD5 Hash</h5>
        {bufferToHex(file.hash)}
      </Column>
    </Row>
    <Row>
      <Column>
        <h5>Tags</h5>
        <ul>
          {#each Object.entries(file.tags) as [key, value]}
            <li><strong>{key}</strong> = {value}</li>
          {/each}
          <ul />
        </ul></Column
      >
      <Column>
        {#if file.headerColumns}
          <h5>Detected Header Columns</h5>
          {file.headerColumns.join(', ')}
        {/if}
      </Column>
    </Row>
  </Grid>
</div>

<ProcessingLogsTable bind:logs={file.log} />

<style>
  .id {
    font-size: 50%;
  }

  .file_details {
    display: flex;
    margin: 30px 0;
    justify-content: space-between;
  }

  .file_details > :global(.bx--grid) {
    flex-grow: 1;
  }

  .file_details :global(.bx--grid) {
    margin: 0 0 0 80px;
    padding: 0;
  }

  .file_details :global(.bx--row) {
    margin-bottom: 3rem;
  }

  .file_details :global(.bx--col) {
    width: 50%;
  }

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
</style>
