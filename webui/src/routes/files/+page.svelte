<script lang="ts">
  import { page } from '$app/stores';
  import type { PageData } from './$types';

  import {
    Breadcrumb,
    BreadcrumbItem,
    Button,
    ComboBox,
    Modal
  } from 'carbon-components-svelte';

  import Add from 'carbon-icons-svelte/lib/Add.svelte';

  import { SvelteDataTable } from '@mac-barrett/svelte-data-table';
  import type { JsonValue } from '@bufbuild/protobuf';

  import { File_Status } from '$lib/rivoli/protos/processing_pb';
  import { Partner, FileType } from '$lib/rivoli/protos/config_pb';

  import Upload from '$lib/components/FileProcessing/Upload.svelte';

  export let data: PageData;
  const partnerMap = data.partnerMap;

  let modalOpen = false;

  const filetypeMap = new Map(
    Array.from(partnerMap.values()).flatMap((p) =>
      Partner.fromJson(p as any as JsonValue).fileTypes.map((ft) => [
        ft.id,
        ft.toJson() as any as FileType
      ])
    )
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

  function renderPartnerName(data, type: string, row) {
    return `<a href="/partners/${row.partnerId}">${
      partnerMap.get(row.partnerId).name
    }</a>`;
  }

  function renderFileTypeName(data, type: string, row) {
    return `<a href="/partners/${row.partnerId}/filetypes/${row.fileTypeId}">${
      filetypeMap.get(row.fileTypeId).name
    }</a>`;
  }

  function renderStatus(data, type: string, row) {
    return File_Status[row.status] || '';
  }

  let config = {
    paging: true,
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
        data: 'id',
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

  function uploadFile(evt: CustomEvent) {
    console.log(evt.detail);
    let formData = new FormData();

    formData.append('file', evt.detail.fileFS);
    formData.append('partnerId', evt.detail.partnerId);
    formData.append('filetypeId', evt.detail.filetypeId);

    console.log(formData);

    fetch($page.url.pathname, { method: 'POST', body: formData });
  }
</script>

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
