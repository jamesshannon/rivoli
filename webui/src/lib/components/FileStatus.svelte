<script lang="ts">

import {
  Tag
} from "carbon-components-svelte";

import { File_Status, type File, type RecordStats } from "$lib/protos/processing_pb";



export let file: File;

// new -> show str in tag, don't do anything
// LOADING - show chart with  records / approxRecords
// LOADED - tag
// PARSING -

// config variable
// : display
// : tag_color
// : errors percent
// : loading percent

function notZero(n) {
  return !n ? 0.001 : n;
}

function sum(stats: RecordStats, prefix: string): number {
  return stats[`${prefix}Success`] + stats[`${prefix}Error`];
}


const status = statuses.get(file.status)!;
console.log(status.success_pct(file.stats));


//   [
//     (stats: RecordStats) => stats.loadedRecords / stats.approximateRows,
//   ],
//   'PARSING': [(stats: RecordStats) => (stats.parsedRecordsSuccess + stats.parsedRecordsError) / stats.approximateRows],
//   'VALIDATING': [(stats: RecordStats) => stats.loadedRecords / stats.approximateRows],
//   'PROCESSING': (stats: RecordStats) => stats.loadedRecords / stats.approximateRows,
// }

</script>

<div class="local">

  <Tag class={true || status.working ? "working" : ''}>{status.label}</Tag>
</div>

<style>
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
