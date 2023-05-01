<script lang="ts">
  import { page } from '$app/stores';

  import {
    Breadcrumb,
    BreadcrumbItem,
    Button,
    Dropdown,
    Modal
  } from 'carbon-components-svelte';

  import { onMount } from 'svelte';

  import type { PageData } from './$types';

  import { SvelteDataTable } from '@mac-barrett/svelte-data-table';

  import { dateTime, escapeHTML, syntaxHighlight } from '$lib/helpers/utils';
  import { type Partner, FileType } from '$lib/rivoli/protos/config_pb';
  import {
    File,
    File_Status,
    Record,
    RecordStats,
    Record_RecordTypeRef,
    Record_Status
  } from '$lib/rivoli/protos/processing_pb';
  import {
    REVERTABLE_MAP,
    RecordsFilter
  } from '$lib/helpers/file_processing/records';
  import Records from '$lib/components/FileProcessing/Records.svelte';

  export let data: PageData;
  let file = File.fromJson(data.file as any, { ignoreUnknownFields: true });
  const filetype = FileType.fromJson(data.fileType as any, {
    ignoreUnknownFields: true
  });
  const recordTypes = new Map(filetype.recordTypes.map((rt) => [rt.id, rt]));

  const statusDropdownAllOption = { id: '', text: 'All Statuses' };
  let statusDropdownOptions: Array<any> = [statusDropdownAllOption];
  let retryModalOpen = false;
  let revertModalEnabled = false;

  // These are values for the ProcessingLog.errorCode enum value. Ideally we'd
  // use that generated enum, but in this case the value might be an HTTP status
  // code (e.g., 502) which is not a defined enum value (though are reserved).
  const processingLogErrorCodes = new Map([
    [600, 'Validation Error'],
    [700, 'Operation Error'],
    [800, 'Execution Error'],
    [801, 'Connection Error'],
    [802, 'Timeout Error']
  ]);

  let filter = new RecordsFilter();
  let filteredResultCount = 0;
  let statusCounts: Map<string, number> = new Map();

  async function retrieveRecords(requestData, callback, settings) {
    console.log(requestData, settings);
    console.log(requestData.columns[3]);

    const fetchParams = new URLSearchParams({
      start: requestData.start,
      length: requestData.length,
      ...filter.filterObj
    });

    const resp = await fetch($page.url.pathname + '?' + fetchParams);
    const result: any = await resp.json();

    const records = [];
    const recordIdMask = (1n << 32n) - 1n;

    for (let record of result.records) {
      // do some conversion
      record.num = BigInt(record.id) & recordIdMask;

      if (record.recordType < 1000) {
        record.recordType = Record_RecordTypeRef[record.recordType];
      } else {
        record.recordType = recordTypes.get(record.recordType)?.name || '';
      }

      record.status = Record_Status[record.status];

      records.push(record);
    }

    statusCounts = new Map(Object.entries(result.statusCounts));
    // statusDropdownOptions = [statusDropdownAllOption].concat(
    //   Object.entries(result.statusCounts).map(([status, cnt]) => ({
    //     id: status,
    //     text: `${Record_Status[status]} (${cnt})`
    //   }))
    // );

    // if (filter.status) {
    //   filteredResultCount = result.statusCounts[filter.status] || 0;
    // } else {
    //   filteredResultCount = file.stats?.totalRows || 0;
    // }

    console.log(records[3]);

    callback({
      draw: parseInt(requestData.draw),
      data: records,
      recordsTotal: file.stats?.totalRows || 0,
      recordsFiltered: filteredResultCount
    });
  }

  function renderLogList(logs: Array<any>) {
    let html = '<ul>';
    for (let log of logs) {
      html += `<li>
        <h6>${escapeHTML(log.message)}</h6>
        <span>${dateTime(log.time)}</span> -
				${processingLogErrorCodes.get(log.errorCode) || log.errorCode || ''}
			</li>`;
    }
    return html + '</ul>';
  }

  function renderRowNum(data, type: string, row) {
    if (type === 'display') {
      return `<div title="${row.id}">${row.num}</div>`;
    }

    return row.num;
  }

  function renderErrors(data, type: string, row) {
    if (type === 'display' || type === 'filter') {
      // Only show recent errors in the table column
      if (row.recentErrors?.length) {
        return renderLogList(row.recentErrors);
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
        '<div><h5>Raw Columns</h5><pre>' +
          data.rawColumns
            .map((str: string) => `<span class="raw">${str}</span>`)
            .join(',') +
          '</pre></div>'
      );
    }
    if (data.parsedFields) {
      lines.push(
        '<div><h5>Parsed Fields</h5><pre class="pretty_json">' +
          syntaxHighlight(data.parsedFields) +
          '</pre></div>'
      );
    }
    if (data.validatedFields) {
      lines.push(
        '<div><h5>Validated Fields</h5><pre class="pretty_json">' +
          syntaxHighlight(data.validatedFields) +
          '</pre></div>'
      );
    }
    if (data.log?.length) {
      lines.push('<div><h5>Log</h5>' + renderLogList(data.log) + '</div>');
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
    dom: 'lrtip', // hide the search box
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
        title: 'Row',
        data: null,
        render: renderRowNum
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
    // if (statusSelectedId != statusLastSelectedId) {
    //
    //   const column = myDataTable.getAPI()?.column('status:name')!;
    //   column.search(statusSelectedId === 'none' ? '' : statusSelectedId).draw();
    // }
    // statusLastSelectedId = statusSelectedId;

    // determine when Retry button is allowed. Only when status is selected and
    // UPLOAD_ERROR and file is not currently processing
  }
  function filterStatusSelected() {
    console.log('selected', filter.filterObj);

    // If the dropdown has items then the data table should be fully loaded
    myDataTable
      .getAPI()
      ?.column('status:name')!
      .search(filter.status === '0' ? '' : filter.status)
      .draw();

    //
  }

  async function revertRecordStatuses(evt: CustomEvent) {
    console.log('clicked', evt, filter.filterObj);

    if (!revertModalEnabled) {
      return;
    }

    const resp = await fetch($page.url.pathname, {
      method: 'POST',
      body: JSON.stringify({
        action: 'REVERT',
        toStatus: revertToId,
        ...filter.filterObj
      })
    });

    const response = await resp.json();

    filter.reset();
    filterStatusSelected();
    retryModalOpen = false;
    alert(JSON.stringify(response));
  }

  let revertToDropdownOptions: Array<{ id: string; text: string }> = [];
  let revertToId: string;

  $: {
    let statuses = REVERTABLE_MAP.get(parseInt(filter.status));
    revertModalEnabled = !!statuses;

    if (statuses) {
      revertToDropdownOptions = statuses.map((s) => ({
        id: s.toString(),
        text: Record_Status[s]
      }));

      revertToId =
        revertToDropdownOptions[revertToDropdownOptions.length - 1].id;
    }
  }
  onMount(async () => {
    console.log(myDataTable.getAPI());
  });

  $: console.log(filter.status);
</script>

<Breadcrumb noTrailingSlash>
  <BreadcrumbItem href="/">Home</BreadcrumbItem>
  <BreadcrumbItem href="/files">File Processing</BreadcrumbItem>
  <BreadcrumbItem href="/files/{file.id}">{file.name}</BreadcrumbItem>
  <BreadcrumbItem isCurrentPage>Records</BreadcrumbItem>
</Breadcrumb>

<Records {file} {filetype} {statusCounts} bind:filter />

<div class="localmodal">
  <Modal
    bind:open={retryModalOpen}
    modalHeading="Revert Records"
    primaryButtonText="Confirm"
    secondaryButtonText="Cancel"
    on:click:button--primary={revertRecordStatuses}
    on:click:button--secondary={() => (retryModalOpen = false)}
  >
    Revert {filteredResultCount} records to <Dropdown
      size="sm"
      type="inline"
      items={revertToDropdownOptions}
      selectedId={revertToId}
    />?
    <p>
      Reverting the record status will cause these {filteredResultCount} records
      and the file status to be reset.
    </p>
  </Modal>
</div>

<div class="local" on:click={expandRowHandler}>
  <SvelteDataTable bind:this={myDataTable} {config} />
</div>

<style>
  #filters {
    margin: 10px;
    border: 1px solid blue;
    padding: 10px;
  }

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
    margin: 0 10px;
    padding: 5px 10px;
    background-color: rgba(128, 128, 128, 0.1);
  }

  .local :global(div.expanded_row pre) {
    font-family: Consolas, 'Andale Mono WT', 'Andale Mono', 'Lucida Console',
      'Lucida Sans Typewriter', 'DejaVu Sans Mono', 'Bitstream Vera Sans Mono',
      'Liberation Mono', 'Nimbus Mono L', Monaco, 'Courier New', Courier,
      monospace;
    white-space: pre-wrap;
  }

  .local :global(div.expanded_row span.raw) {
    background-color: rgba(0, 0, 0, 0.1);
  }

  .local :global(.pretty_json .string) {
    color: green;
  }
  .local :global(.pretty_json .number) {
    color: darkorange;
  }
  .local :global(.pretty_json .boolean) {
    color: blue;
  }
  .local :global(.pretty_json .null) {
    color: magenta;
  }
  .local :global(.pretty_json .key) {
    color: red;
  }

  .localmodal :global(.bx--dropdown__wrapper--inline) {
    position: relative;
    top: -5px;
    grid-gap: 0;
    gap: 0;
  }

  .localmodal :global(.bx--modal-content) {
    overflow-y: visible;
  }
</style>
