<script lang="ts">
  import { page } from '$app/stores';
  import type { PageData } from './$types';

  import { SvelteDataTable } from '@mac-barrett/svelte-data-table';

  import {
    getTableConfig,
    makeDynamicColumns
  } from '$lib/helpers/file_processing/records_table';

  export let data: PageData;
  const { file, partner, outputInst, output } = data;

  async function retrieveRecords(requestData, callback, settings) {
    // create query params for the record

    const fetchParams = new URLSearchParams({
      start: requestData.start,
      length: requestData.length
    });

    const resp = await fetch($page.url.pathname + '?' + fetchParams);
    const result: any = await resp.json();

    callback({
      draw: parseInt(requestData.draw),
      data: result.records,
      recordsTotal: result.count,
      recordsFiltered: result.count
    });
  }

  // generate the columns list
  // row number, configured columns (probably from validated Fields)
  // possible checkbox

  let recordsDataTable: SvelteDataTable;
  const dtConfig = getTableConfig(
    retrieveRecords,
    makeDynamicColumns(file.validatedColumns, true)
  );

  dtConfig.scrollX = true;

  console.log(dtConfig);
</script>

<div class="local">
  <SvelteDataTable bind:this={recordsDataTable} config={dtConfig} />
</div>


<style>
  .local :global(td.record_field) {
    font-family: 'Courier New', Courier, monospace;
  }
  </style>
