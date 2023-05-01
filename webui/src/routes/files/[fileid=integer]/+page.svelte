<script lang="ts">
  import { page } from '$app/stores';

  import {
    Button,
    Breadcrumb,
    BreadcrumbItem,
    Grid,
    Row,
    Column,
    Tag
  } from 'carbon-components-svelte';

  import type { PageData } from './$types';
  import { invalidateAll } from '$app/navigation';

  import ProcessingLogsTable from '$lib/components/ProcessingLogsTable.svelte';
  import PrettyJson from '$lib/components/PrettyJson.svelte';

  import { fmtNum } from '$lib/helpers/utils';
  import { statuses } from '$lib/helpers/files';
  import { onMount } from 'svelte';

  import { type Partner, FileType } from '$lib/rivoli/protos/config_pb';
  import { File_Status, File } from '$lib/rivoli/protos/processing_pb';
  import Outputs from '$lib/components/FileProcessing/Outputs.svelte';
  import Progress from '$lib/components/FileProcessing/Progress.svelte';

  export let data: PageData;
  let file: File;
  const filetype = FileType.fromJson(data.fileType as any, {
    ignoreUnknownFields: true
  });
  function setFileFromData() {
    file = File.fromJson(data.file as any, { ignoreUnknownFields: true });
  }
  setFileFromData();

  onMount(() => {
    refreshFile();
  });

  function refreshFile(timeout_ms?: number) {
    const refresh_time =
      timeout_ms || (statuses.get(file.status)?.working ? 15_000 : 60_000);

    async function refreshFileData() {
      // invalidate($page.url) does not work, so we invalidate everything
      await invalidateAll();
      setFileFromData();
    }

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

  // Needs to be encapsulated
  let statusString: string;
  let statusIsWorking: boolean;
  $: statusString = File_Status[file.status];
  $: statusIsWorking = statuses.get(file.status)?.working || false;

  async function doFileAction(body: any) {
    /* POST action request for this File */
    const resp = await fetch($page.url.pathname, {
      method: 'POST',
      body: JSON.stringify(body)
    });

    const response = await resp.json();
    //alert(JSON.stringify(response));
    console.log(response);

    // force refresh of File
    refreshFile(1_000);
  }

  function runReport(evt: CustomEvent) {
    console.log(evt.detail);
    doFileAction({ action: 'EXECUTE_REPORT', outputId: evt.detail.outputId });
  }

  async function approveFileUploading() {
    // Make request ot server to update the file status and schedule
    // processing. In the future this might need to be abstracted to handle
    // different statuses.
    doFileAction({ action: 'APPROVE_UPLOAD' });
  }
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
<div class="local">
  <Tag class={statusIsWorking ? 'working' : ''}>{statusString}</Tag>
  {#if file.status == File_Status.WAITING_APPROVAL_TO_UPLOAD}
    <Button on:click={approveFileUploading}>Upload Records</Button>
  {/if}
</div>

<div class="file_details">
  <Progress {file} />
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
        <PrettyJson json={file.tags} />
      </Column>
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

{#if file.status >= File_Status.UPLOADED}
  <h3>Reports</h3>
  <Outputs {file} {filetype} on:runReport={runReport} />
{/if}

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

  .local :global(.working) {
    background-color: #222;
    animation-name: pulsing;
    animation-duration: 1s;
    animation-iteration-count: infinite;
  }

  @keyframes pulsing {
    0% {
      background-color: #5c8ddb;
    }
    50% {
      background-color: #4285f4;
    }
    100% {
      background-color: #5c8ddb;
    }
  }
</style>
