<script lang="ts">

import {
  DataTable
} from "carbon-components-svelte";


import type { ProcessingLog } from "$lib/protos/processing_pb";

import {dateTime} from "$lib/helpers/utils";

export let logs: Array<ProcessingLog>;

let headers = [
  {key: 'time', value: 'Date'},
  {key: 'source', value: 'Source'},
  {key: 'message', value: 'Message' },
];

let rows = logs.reverse().map((pl) => {return {id: pl.time, time: pl.time, source: pl.source, message: pl.message}});

</script>

<DataTable pageSize={10} bind:headers bind:rows>
  <svelte:fragment slot="cell" let:row let:cell>
    {#if cell.key === "time"}
      {dateTime(cell.value)}
    {:else}
      {cell.value}
    {/if}
  </svelte:fragment>
</DataTable>
