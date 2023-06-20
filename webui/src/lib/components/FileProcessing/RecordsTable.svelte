<script lang="ts">
  import { page } from '$app/stores';

  import {
      Button,
    Checkbox,
    InlineNotification,
    NotificationActionButton
  } from 'carbon-components-svelte';

  import { SvelteDataTable } from '@mac-barrett/svelte-data-table';

  import { RecordsFilter } from '$lib/helpers/file_processing/records';
  import {
    Record_RecordTypeRef,
    type File,
    Record_Status,
    File_Status
  } from '$lib/rivoli/protos/processing_pb';
  import type { FileType } from '$lib/rivoli/protos/config_pb';
  import {
    fileDetailLeftColumns,
    errorsColumn,
    getTableConfig,
    makeExpandedRow,
    makeDynamicColumns
  } from '$lib/helpers/file_processing/records_table';

  import RecordFilter from '$lib/components/FileProcessing/RecordFilter.svelte';

  interface ColumnGroup {
    key?: string;
    title?: string;
    visible: boolean;
    length: number;
  }

  export let file: File;
  export let filetype: FileType;

  let recordsDataTable: SvelteDataTable;
  let recordFilterInstance: any;

  const recordTypes = new Map(filetype.recordTypes.map((rt) => [rt.id, rt]));

  // Generate the column configuration
  const columns: Array<object> = [];

  const columnGroups: Array<ColumnGroup> = [];
  let columnGroupParsed: ColumnGroup | undefined;
  let columnGroupValidated: ColumnGroup | undefined;

  columns.push(...fileDetailLeftColumns);
  columnGroups.push({visible: true, length: columns.length});

  if (file.status >= File_Status.PARSED && file.parsedColumns.length) {
    const cols = makeDynamicColumns(file.parsedColumns, 'parsedFields');
    columns.push(...cols);
    columnGroupParsed =
        {key: 'parsedFields', title: 'Parsed Fields', visible: false, length: cols.length};
    columnGroups.push(columnGroupParsed);
  }
  if (file.status >= File_Status.VALIDATED && file.validatedColumns.length) {
    const cols = makeDynamicColumns(file.validatedColumns, 'validatedFields');
    columns.push(...cols);
    columnGroupValidated =
        {key: 'validatedFields', title: 'Validated Fields', visible: false, length: cols.length};
    columnGroups.push(columnGroupValidated);
  }

  columns.push(...errorsColumn);
  columnGroups.push({visible: true, length: 1});

  function removeGroupHeader() {
    document.getElementById('table_group_header')?.remove();
  }

  function resetGroupHeader(tr: HTMLElement) {
    let thead = tr.parentElement!;

    // Possibly remove the group header row
    removeGroupHeader();

    // Add a new group header row
    const tags = ['<tr id="table_group_header" class="groups">',
        ...columnGroups
            .filter((g) => g.visible)
            .map((g) => `<th colspan="${g.length}">${g.title || ''}</th>`),
        '</tr>'];

    thead.insertAdjacentHTML('afterbegin', tags.join(''));
  }

  function updateColumnGroupVisibility() {
    removeGroupHeader();

    const api = recordsDataTable?.getAPI();
    for (let group of [columnGroupParsed, columnGroupValidated]) {
      if (group) {
        api?.columns(`.${group.key}`).visible(group?.visible)
      }
    }

    resizeTable();
  }


  const dtConfig = getTableConfig(retrieveRecords, columns);
  dtConfig.headerCallback = resetGroupHeader;

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
    recordsDataTable?.getAPI()?.columns.adjust().draw('page');
  }

  function updateDatatableFilter() {
    // Filter & redraw the datatable when the dropdown is changed
    // This causes the datatable to call retrieveRecords()
    // Can't use reactivity because this causes `filter` to be updated
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

    filter.text = requestData.search.value;

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

    // Update the returned records
    for (let record of result.data.records) {
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
    statusCounts = new Map(Object.entries(result.data.statusCounts));

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
      filter.resultCount = Array.from(statusCounts.values())
          .reduce((a, b) => a + b, 0);
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

{#if columnGroupParsed}
  <Checkbox labelText="Parsed Fields" bind:checked={columnGroupParsed.visible} on:check={updateColumnGroupVisibility} />
{/if}
{#if columnGroupValidated}
  <Checkbox labelText="Validated Fields" bind:checked={columnGroupValidated.visible} on:check={updateColumnGroupVisibility} />
{/if}

<div class="local" on:click={expandRowHandler} on:keypress={expandRowHandler}>
  <SvelteDataTable bind:this={recordsDataTable} config={dtConfig} />
</div>



<style>
  .local :global(thead th) {
    vertical-align: bottom;
  }

  .local :global(thead tr.groups th:empty) {
    border: 0;
  }

  .local :global(#table_wrapper .controls) {
    display: flex;
    justify-content: space-between;
  }

  .local :global(#table_wrapper .controls > div) {
    float: none;
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

  .local :global(td.record_field) {
    white-space: pre;
    font-family: 'Courier New', Courier, monospace;
  }

  .local :global(td.errors) {
    white-space: nowrap;
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
