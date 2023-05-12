<script lang="ts">
  import { page } from '$app/stores';

  import {
    Button,
    Breadcrumb,
    BreadcrumbItem,
    Tabs,
    Tab,
    TabContent,
    Tag
  } from 'carbon-components-svelte';

  import type { PageData } from './$types';
  import { invalidateAll } from '$app/navigation';

  import { onMount } from 'svelte';

  import { FileType } from '$lib/rivoli/protos/config_pb';
  import { Function } from '$lib/rivoli/protos/functions_pb';
  import { File_Status, File } from '$lib/rivoli/protos/processing_pb';

  import Details from '$lib/components/FileProcessing/Details.svelte';
  import Outputs from '$lib/components/FileProcessing/Outputs.svelte';
  import RecordsTable from '$lib/components/FileProcessing/RecordsTable.svelte';
  import StatusTag from '$lib/components/FileProcessing/StatusTag.svelte';
  import ProcessingLogsTable from '$lib/components/ProcessingLogsTable.svelte';

  import { statuses } from '$lib/helpers/files';
  import Diagram from '$lib/components/FileProcessing/Diagram.svelte';

  function setFileFromData() {
    let newFile = File.fromJson(data.file as any, {
      ignoreUnknownFields: true
    });
    // Only update the file if it has changed. This prevents other a lot of
    // code from unnecessarily reacting on every refresh.
    if (!newFile.equals(file)) {
      file = newFile;
    }
  }

  export let data: PageData;
  let file: File;
  setFileFromData();

  const filetype = FileType.fromJson(data.fileType as any, {
    ignoreUnknownFields: true
  });

  let functions = new Map(
    data.functions.map((f) => [f.id, Function.fromJson(f as any)])
  );

  let recordsTableInstance: any;
  let selectedTabIdx = 0;

  onMount(() => {
    refreshFile();
  });

  function refreshFile(timeout_ms?: number) {
    const refresh_time =
      timeout_ms || (statuses.get(file.status)?.working ? 10_000 : 60_000);

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

  async function revertRecordStatuses(evt: CustomEvent) {
    const resp = await fetch($page.url.pathname, {
      method: 'POST',
      body: JSON.stringify({
        action: 'REVERT_RECORDS',
        toStatus: evt.detail.revertToId,
        ...evt.detail.filter.filterObj
      })
    });

    const response = await resp.json();

    recordsTableInstance.resetFilters();
    selectedTabIdx = 0;

    alert(JSON.stringify(response));
  }

  let res;
  const diagramVisiblePromise: Promise<boolean> = new Promise(
    (resolve, reject) => {
      res = resolve;
    }
  );
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
  <StatusTag {file} />
  {#if file.status == File_Status.WAITING_APPROVAL_TO_UPLOAD}
    <Button on:click={approveFileUploading}>Upload Records</Button>
  {/if}
</div>

<Tabs selected={selectedTabIdx}>
  <Tab label="Details" />
  <Tab
    label="Graph"
    on:click={() => {
      setTimeout(res, 100);
    }}
  />
  <Tab label="Records" on:click={() => recordsTableInstance.resizeTable()} />
  <Tab label="Logs" />
  {#if file.status >= File_Status.UPLOADED}<Tab label="Reports" />{/if}

  <svelte:fragment slot="content">
    <!-- Tab: Details -->
    <TabContent>
      <Details {file} />
    </TabContent>

    <!-- Tab: Graph -->
    <TabContent class="graph">
      <Diagram
        {file}
        {filetype}
        {functions}
        visiblePromise={diagramVisiblePromise}
      />
    </TabContent>

    <!-- Tab: Records -->
    <TabContent>
      <RecordsTable
        {file}
        {filetype}
        on:revert={revertRecordStatuses}
        bind:this={recordsTableInstance}
      />
    </TabContent>

    <!-- Tab: Logs -->
    <TabContent>
      <ProcessingLogsTable bind:logs={file.log} />
    </TabContent>

    <!-- Tab: Reports -->
    {#if file.status >= File_Status.UPLOADED}
      <TabContent>
        <Outputs {file} {filetype} on:runReport={runReport} />
      </TabContent>
    {/if}
  </svelte:fragment>
</Tabs>

<style>
  .id {
    font-size: 50%;
  }

  :global(.graph) {
    height: 100%;
    min-height: 500px;
  }
</style>
