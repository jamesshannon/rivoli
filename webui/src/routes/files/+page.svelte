<script lang="ts">
  import { page } from '$app/stores';
  import type { PageData } from './$types';

  import {
    Breadcrumb,
    BreadcrumbItem,
    Button,
  } from 'carbon-components-svelte';

  import Add from 'carbon-icons-svelte/lib/Add.svelte';

  import { SvelteDataTable } from '@mac-barrett/svelte-data-table';

  import { File_Status } from '$lib/rivoli/protos/processing_pb';
  import { Partner } from '$lib/rivoli/protos/config_pb';

  import Notification from '$lib/components/Notification.svelte';
  import Upload from '$lib/components/FileProcessing/Upload.svelte';

  export let data: PageData;
  const partnerMap = new Map(data.partners.map(p => [p.id, Partner.fromJson(p as any)]));

  let modalOpen = false;
  let notificationElement: Notification;

  const filetypeMap = new Map(
    Array.from(partnerMap.values()).flatMap((p) =>
        p.fileTypes.map((ft) => [ft.id, ft]))
  );

  function renderFileName(data, type: String, row) {
    if (type === 'display') {
      return `<a href="/files/${row['id']}">${row['name']}</a>`;
    }

    return data;
  }

  function renderDate(data, type: string, row) {
    if (type === 'display') {
      return new Date(row['created'] * 1000).toLocaleString([], {
        dateStyle: 'short',
        timeStyle: 'short'
      });
    }

    return data;
  }

  function renderRecordCount(data, type: String, row) {
    if (type === 'display') {
      return row.stats?.totalRows
        ? row.stats.totalRows
        : `~ ${row.stats.approximateRows}`;
    }

    return data;
  }

  function renderPartnerName(_, type: string, row) {
    return `<a href="/partners/${row.partnerId}">${
      partnerMap.get(row.partnerId).name
    }</a>`;
  }

  function renderFileTypeName(_, type: string, row) {
    return `<a href="/partners/${row.partnerId}/filetypes/${row.fileTypeId}">${
      filetypeMap.get(row.fileTypeId)!.name
    }</a>`;
  }

  function renderStatus(_, type: string, row) {
    return File_Status[row.status] || '';
  }

  let config = {
    paging: true,
    pageLength: 20,
    lengthMenu: [10, 20, 50, 100, 1000],
    searching: true,
    ordering: false,
    //serverSide: true,
    deferRender: true,
    ajax: async (tableData, callback, settings) => {
      // get from server
      callback({ data: data.files, recordsTotal: 1000 });
    },
    columns: [
      {
        title: 'File',
        data: 'name',
        render: renderFileName
      },
      {
        title: 'Partner',
        data: 'partnerId',
        render: renderPartnerName
      },
      {
        title: 'File Type',
        data: 'fileTypeId',
        render: renderFileTypeName
      },
      {
        title: 'Date',
        data: 'created',
        render: renderDate
      },
      {
        title: 'Row Count',
        data: 'status',
        render: renderRecordCount
      },
      {
        title: 'Status',
        data: 'status',
        render: renderStatus
      }
    ]
  };

  async function uploadFile(evt: CustomEvent) {
    let formData = new FormData();

    formData.append('file', evt.detail.fileFS);
    formData.append('partnerId', evt.detail.partnerId);
    formData.append('filetypeId', evt.detail.filetypeId);

    modalOpen = false;
    const resp = await fetch(
        $page.url.pathname, { method: 'POST', body: formData });
    notificationElement.showNotification(await resp.json());
  }
</script>

<Notification bind:this={notificationElement} />

<Breadcrumb noTrailingSlash>
  <BreadcrumbItem href="/">Home</BreadcrumbItem>
  <BreadcrumbItem isCurrentPage>File Processing</BreadcrumbItem>
</Breadcrumb>

<SvelteDataTable {config} />

<Button
  kind="tertiary"
  size="small"
  on:click={() => (modalOpen = true)}
  icon={Add}>Add</Button
>

<Upload {partnerMap} on:upload={uploadFile} bind:modalOpen />
