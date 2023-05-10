<script lang="ts">
  import { Tag } from 'carbon-components-svelte';

  import { type File, File_Status } from '$lib/rivoli/protos/processing_pb';

  import { statuses } from '$lib/helpers/files';

  export let file: File;

  $: statusString = File_Status[file.status];
  $: statusIsWorking = statuses.get(file.status)?.working || false;
</script>

<div class="local">
  <Tag class={statusIsWorking ? 'working' : ''}>{statusString}</Tag>
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
