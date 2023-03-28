<script lang="ts">
  import { page } from '$app/stores';

  import {
    Breadcrumb,
    BreadcrumbItem,
    Button,
    Dropdown
  } from 'carbon-components-svelte';

  import { onMount } from 'svelte';

  import type { PageData } from './$types';

  import FileStatus from '$lib/components/FileStatus.svelte';

  import { SvelteDataTable } from '@mac-barrett/svelte-data-table';

  import { dateTime } from '$lib/helpers/utils';
  import { type Partner, FileType } from '$lib/protos/config_pb';
  import {
    File,
    File_Status,
    Record,
    Record_RecordTypeRef,
    Record_Status
  } from '$lib/protos/processing_pb';

  export let data: PageData;
  let file = File.fromJson(data.file as any);
  const filetype = FileType.fromJson(data.fileType as any);
  const recordTypes = new Map(filetype.recordTypes.map((rt) => [rt.id, rt]));

  const statusDropdownAnyOption = { id: 'none', text: 'All Statuses' };
  let statusDropdownOptions: Array<any> = [statusDropdownAnyOption];
  let statusLastSelectedId = 'none';
  let statusSelectedId = 'none';

  const escape = document.createElement('textarea');
  function escapeHTML(html: string): string {
    escape.textContent = html;
    return escape.innerHTML;
  }

  async function retrieveRecords(requestData, callback, settings) {
    console.log(requestData, settings);
    console.log(requestData.columns[3]);

    const status_filter =
      requestData.columns.find((c) => c.name == 'status').search.value || '';
    console.log(status_filter);

    const fetchParams = new URLSearchParams({
      start: requestData.start,
      length: requestData.length,
      status_filter: status_filter
    });

    const resp = await fetch($page.url.pathname + '?' + fetchParams);
    const result: Array<Record> = await resp.json();

    console.log(result);

    const records = [];
    const recordIdMask = (1n << 32n) - 1n;

    for (let record of result.records) {
      // do some conversion
      record.num = BigInt(record.id) & recordIdMask;

      if (record.recordType < 1000) {
        record.recordType = Record_RecordTypeRef[record.recordType];
      } else {
        record.recordType = recordTypes.get(record.recordType)?.name;
      }

      record.status = Record_Status[record.status];

      records.push(record);
    }

    statusDropdownOptions = [statusDropdownAnyOption].concat(
      Object.entries(result.statusCounts).map(([status, cnt]) => ({
        id: status,
        text: `${Record_Status[status]} (${cnt})`
      }))
    );
    console.log(statusDropdownOptions);

    let filtered_records: number;
    if (status_filter) {
      filtered_records = result.statusCounts[status_filter] || 0;
    } else {
      filtered_records = file.stats?.loadedRecordsSuccess || 0;
    }

    console.log(records[3]);

    callback({
      draw: parseInt(requestData.draw),
      data: records,
      recordsTotal: file.stats?.loadedRecordsSuccess,
      recordsFiltered: filtered_records
    });
  }

  function renderErrorList(errors: Array<any>) {
    let html = '<ul>';
    for (let error of errors) {
      html += '<li>';
      html += escapeHTML(error['message']);
      html += '</li>';
    }
    return html + '</ul>';
  }

  function renderErrors(data, type: string, row) {
    if (type === 'display' || type === 'filter') {
      // Only show recent errors for now...
      if (row.recentErrors?.length) {
        return renderErrorList(row['recentErrors']);
      }
    }

    return '';
  }

  // What to show?
  // NEW - Not much
  // LOADED - recordType, status, errors, rawColumns (or rawLine)
  // PARSED - parsedFields dict
  // VALIDATED - validatedFields dict (this is the final dict, but
  //   it's per record type, and might have even been changed by the  validators
  //   maybe loop through the first 100 (?) records (by record id) and build the
  //   column list?
  //

  function makeExpandedRow(data): string {
    const lines = [];
    if (data.rawColumns) {
      lines.push(
        '<div><h5>Raw Columns</h5>' +
          data.rawColumns
            .map((str: string) => `<span>${str}</span>`)
            .join(',') +
          '</div>'
      );
    }
    if (data.parsedFields) {
      lines.push(
        '<div><h5>Parsed Fields</h5>' +
          JSON.stringify(data.parsedFields, null, 2) +
          '</div>'
      );
    }
    if (data.validatedFields) {
      lines.push(
        '<div><h5>Validated Fields</h5>' +
          JSON.stringify(data.validatedFields, null, 2) +
          '</div>'
      );
    }

    if (data.log?.length) {
      lines.push('<div><h5>Log</h5>' + renderErrorList(data.log) + '</div>');
    }

    return '<div class="expanded_row">' + lines.join('') + '</div>';
  }

  function expandRowHandler(evt: MouseEvent) {
    if ((evt.target as HTMLElement).classList.contains('expand-button')) {
      let tr = (evt.target as HTMLElement).parentElement!.parentElement!;
      let row = myDataTable.getAPI()?.row(tr)!;

      if (row.child.isShown()) {
        row.child.hide();
        tr.classList.remove('expanded');
      } else {
        tr.classList.add('expanded');
        row.child(makeExpandedRow(row.data())).show();
      }
    }
  }

  let config = {
    paging: true,
    pageLength: 10,
    searching: true,
    dom: 'lrtip',
    ordering: false,
    serverSide: true,
    deferRender: true,
    ajax: retrieveRecords,
    columns: [
      {
        className: 'table-expandrow',
        orderable: false,
        data: null,
        defaultContent: '<div class="expand-button"></div>'
      },
      {
        title: 'Record',
        data: 'num'
      },
      {
        title: 'Record Type',
        data: 'recordType'
      },
      {
        title: 'Status',
        name: 'status',
        data: 'status'
      },
      {
        title: 'Recent Errors',
        data: null,
        render: renderErrors
      }
    ]
  };

  let myDataTable: SvelteDataTable;

  $: {
    console.log('dropdown changed');
    if (statusSelectedId != statusLastSelectedId) {
      // If the dropdown has items then the data table should be fully loaded
      const column = myDataTable.getAPI()?.column('status:name')!;
      column.search(statusSelectedId === 'none' ? '' : statusSelectedId).draw();
    }
    statusLastSelectedId = statusSelectedId;
  }

  onMount(async () => {
    console.log(myDataTable.getAPI());
  });
</script>

<Breadcrumb noTrailingSlash>
  <BreadcrumbItem href="/">Home</BreadcrumbItem>
  <BreadcrumbItem href="/files">File Processing</BreadcrumbItem>
  <BreadcrumbItem href="/files/{file.id}">{file.name}</BreadcrumbItem>
  <BreadcrumbItem isCurrentPage>Records</BreadcrumbItem>
</Breadcrumb>

<Dropdown
  type="inline"
  titleText="Status"
  bind:items={statusDropdownOptions}
  bind:selectedId={statusSelectedId}
/>

<div class="local" on:click={expandRowHandler}>
  <SvelteDataTable bind:this={myDataTable} {config} />
</div>

<style>
  .local :global(div.expand-button) {
    cursor: pointer;
    position: relative;
    width: 15px;
    height: 15px;
  }

  .local :global(div.expand-button:before),
  .local :global(div.expand-button:after) {
    content: '';
    position: absolute;
    background-color: darkgray;
    transition: transform 0.25s ease-out;
  }

  /* vertical line */
  .local :global(div.expand-button:before) {
    top: 0;
    left: 50%;
    width: 4px;
    height: 100%;
    margin-left: -2px;
  }

  /* horizontal line */
  .local :global(div.expand-button::after) {
    top: 50%;
    left: 0;
    width: 100%;
    height: 4px;
    margin-top: -2px;
  }

  .local :global(div.expand-button:hover:before),
  .local :global(div.expand-button:hover:after) {
    background-color: rgb(126, 135, 169);
  }

  .local :global(tr.expanded div.expand-button:before) {
    transform: rotate(90deg);
  }

  .local :global(tr.expanded div.expand-button:after) {
    transform: rotate(180deg);
  }

  .local :global(div.expanded_row) {
    font-family: Consolas, 'Andale Mono WT', 'Andale Mono', 'Lucida Console',
      'Lucida Sans Typewriter', 'DejaVu Sans Mono', 'Bitstream Vera Sans Mono',
      'Liberation Mono', 'Nimbus Mono L', Monaco, 'Courier New', Courier,
      monospace;
    white-space: pre-wrap;
  }

  .local :global(div.expanded_row span) {
    background: #dddddd;
  }
</style>
