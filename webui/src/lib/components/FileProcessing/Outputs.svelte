<script lang="ts">
  import { createEventDispatcher } from 'svelte';

  import { Button, DataTable, Dropdown } from 'carbon-components-svelte';

  import type { FileType, Output } from '$lib/rivoli/protos/config_pb';
  import {
    OutputInstance_Status,
    type File,
    OutputInstance
  } from '$lib/rivoli/protos/processing_pb';
  import { dateTime, makeObjectId } from '$lib/helpers/utils';
  import type { Message } from '@bufbuild/protobuf';
  import { Download } from 'carbon-icons-svelte';

  export let file: File;
  export let filetype: FileType;

  const dispatch = createEventDispatcher();

  function runReport() {
    dispatch('runReport', { outputId: outputId });
    outputId = '';
  }

  let headers = [
    { key: 'startTime', value: 'Date' },
    { key: 'outputId', value: 'Report' },
    { key: 'outputFilename', value: 'File' },
    { key: 'status', value: 'Status' }
  ];

  let rows: OutputInstance[];
  $: rows = file.outputs.reverse();

  const outputItems = [{ id: '', text: 'Choose Report' }].concat(
    filetype.outputs.map((o) => ({ id: o.id, text: o.name }))
  );

  let outputId = '';
</script>

<DataTable size="short" pageSize={10} bind:headers bind:rows>
  <svelte:fragment slot="cell" let:row let:cell>
    {#if cell.key === 'startTime'}
      {dateTime(cell.value)}
    {:else if cell.key === 'status'}
      {OutputInstance_Status[cell.value]}
    {:else if cell.key === 'outputId'}
      {filetype.outputs.find((o) => o.id === cell.value)?.name}
    {:else if cell.key === 'outputFilename'}
      <Button
        size="small"
        kind="tertiary"
        icon={Download}
        iconDescription="Download"
        href="/files/{file.id}/reports/{row.id}/download"
      />
      {cell.value}
    {:else}
      {cell.value}
    {/if}
  </svelte:fragment>
</DataTable>

<Dropdown type="inline" items={outputItems} bind:selectedId={outputId} />
<Button
  size="field"
  kind="tertiary"
  disabled={outputId == ''}
  on:click={runReport}>Run Report</Button
>
