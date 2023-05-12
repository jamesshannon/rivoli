<script lang="ts">
  import { page } from '$app/stores';

  import {
    InlineNotification,
    NotificationActionButton
  } from 'carbon-components-svelte';

  import { SvelteDataTable } from '@mac-barrett/svelte-data-table';

  import { RecordsFilter } from '$lib/helpers/file_processing/records';
  import {
    Record_RecordTypeRef,
    type File,
    Record_Status
  } from '$lib/rivoli/protos/processing_pb';
  import type { FileType } from '$lib/rivoli/protos/config_pb';
  import {
    getTableConfig,
    makeExpandedRow
  } from '$lib/helpers/file_processing/records_table';

  import RecordFilter from '$lib/components/FileProcessing/RecordFilter.svelte';

  export let file: File;
  export let filetype: FileType;

  let recordsDataTable: SvelteDataTable;
  let recordFilterInstance: any;

  const recordTypes = new Map(filetype.recordTypes.map((rt) => [rt.id, rt]));

  const dtConfig = getTableConfig(retrieveRecords);
  let filter = new RecordsFilter();
  let statusCounts: Map<string, number> = new Map();

  let fileUpdatedSinceRecordsLoad = false;

  export function resetFilters() {
    // Expose this function to reset table and filter component filters
    recordFilterInstance.resetFilters();
  }

  export function resizeTable() {
    // The datatable doesn't auto-size correctly if it's instantiated while
    // hidden. Call this to resize.
    document.getElementById('table')!.style.width = '100%';
  }

  function updateDatatableFilter() {
    // Filter & redraw the datatable when the dropdown is changed
    // This causes the datatable to call retrieveRecords()
    // Can't use reactivity because this causes filter to be updated
    recordsDataTable
      ?.getAPI()
      ?.column('status:name')!
      .search(filter.status === '0' ? '' : filter.status)
      .draw();
  }

  async function retrieveRecords(requestData, callback, settings) {
    // Ensure that the 4th column is still the status column
    console.assert(
      requestData.columns[3].data === 'status',
      'Fourth column is unexpected'
    );

    // Create query parameters from the datatables start/limit parameters plus
    // the filter RecordsFilter values
    const fetchParams = new URLSearchParams({
      start: requestData.start,
      length: requestData.length,
      ...filter.filterObj
    });

    const resp = await fetch($page.url.pathname + '?' + fetchParams);
    const result: any = await resp.json();

    // Array of objects to return to the datatable
    const records = [];
    // Constant which allows us to determine the row number from the record id
    const recordIdMask = (1n << 32n) - 1n;

    // Update the returned records
    for (let record of result.records) {
      // Add a 0-based row number value. The row number can be calculated from
      // the file ID and the record ID.
      record.num = BigInt(record.id) & recordIdMask;

      // Convert the recordType to the appropriate enum value
      if (record.recordType < 1000) {
        record.recordType = Record_RecordTypeRef[record.recordType];
      } else {
        record.recordType = recordTypes.get(record.recordType)?.name || '';
      }

      // Convert status to the enum value
      record.status = Record_Status[record.status];

      records.push(record);
    }

    // Update the statusCounts map.
    statusCounts = new Map(Object.entries(result.statusCounts));

    // Calculate the number of records available that match this (possible)
    // filter. This is used by the datatable to show an "... of x entries" and
    // by the filter modal to show how many records will be reverted
    if (filter.status) {
      filter.resultCount = statusCounts.get(filter.status) || 0;
    } else {
      // The API doesn't return the total number of records available; we use
      // the value from the file.stats. Alternatively, we could sum up the
      // values from the statusCounts map.
      filter.resultCount = file.stats?.totalRows || 0;
    }

    fileUpdatedSinceRecordsLoad = false;

    callback({
      draw: parseInt(requestData.draw),
      data: records,
      recordsTotal: file.stats?.totalRows || 0,
      recordsFiltered: filter.resultCount
    });
  }

  function expandRowHandler(evt: MouseEvent | KeyboardEvent) {
    if ((evt.target as HTMLElement).classList.contains('expand-button')) {
      let tr = (evt.target as HTMLElement).parentElement!.parentElement!;
      let row = recordsDataTable.getAPI()?.row(tr)!;

      if (row.child.isShown()) {
        row.child.hide();
        tr.classList.remove('expanded');
      } else {
        tr.classList.add('expanded');
        row.child(makeExpandedRow(row.data())).show();
      }
    }
  }

  // Set this variable to true every time file is updated.
  $: fileUpdatedSinceRecordsLoad = !!file;
</script>

{#if fileUpdatedSinceRecordsLoad}
  <InlineNotification
    lowContrast
    kind="info"
    title="Possible Updates Pending"
    subtitle="The File record has been updated and these records may need to be refreshed"
  >
    <svelte:fragment slot="actions">
      <NotificationActionButton
        on:click={() => recordsDataTable.getAPI()?.ajax.reload()}
        >Refresh</NotificationActionButton
      >
    </svelte:fragment>
  </InlineNotification>
{/if}

<RecordFilter
  {file}
  {filetype}
  {statusCounts}
  {filter}
  on:filtered={updateDatatableFilter}
  on:revert
  bind:this={recordFilterInstance}
/>

<div class="local" on:click={expandRowHandler} on:keypress={expandRowHandler}>
  <SvelteDataTable bind:this={recordsDataTable} config={dtConfig} />
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
</style>
