<script lang="ts">
  import { getContext } from 'svelte';

  import { Button, FormLabel } from 'carbon-components-svelte';

  import Add from 'carbon-icons-svelte/lib/Add.svelte';
  import Edit from 'carbon-icons-svelte/lib/Edit.svelte';
  import Delete from 'carbon-pictograms-svelte/lib/Delete.svelte';

  import type { FunctionConfig } from '$lib/rivoli/protos/config_pb';
  import {
    type Function,
    Function_DataType,
    Function_FunctionType
  } from '$lib/rivoli/protos/functions_pb';
  import FunctionEditorModal from './FunctionEditorModal.svelte';

  export let functionConfig: FunctionConfig | undefined;
  export let functionType: Function_FunctionType | Array<Function_FunctionType>;
  export let labelText: string | undefined;

  let functionsMap: Map<string, Function> = getContext('FUNCTIONS');

  let modalOpen = false;

  function editHandler(evt) {
    modalOpen = true;
  }

  function deleteHandler(evt) {
    functionConfig = undefined;
  }

  function saveChanges(evt) {
    functionConfig = evt.detail.functionConfig;
  }

  $: {
    console.log(functionConfig);
  }
</script>

{#if labelText}
  <FormLabel>{labelText}</FormLabel>
{/if}
<div class="validation_line">
  {#if functionConfig}
    <div class="function">
      {functionsMap.get(functionConfig.functionId)
        ?.name}({functionConfig.parameters.join(', ')})
    </div>
    <Button
      kind="tertiary"
      size="small"
      on:click={editHandler}
      iconDescription="Edit"
      icon={Edit}
    />
    <Button
      size="small"
      kind="tertiary"
      on:click={deleteHandler}
      iconDescription="Remove"
      icon={Delete}
    />
  {:else}
    <div class="function">xxx</div>
    <Button
      kind="tertiary"
      size="small"
      on:click={editHandler}
      iconDescription="Add"
      icon={Add}
    />
  {/if}
</div>

<FunctionEditorModal
  bind:open={modalOpen}
  {functionConfig}
  on:save={saveChanges}
  {functionType}
/>

<style>
  .validation_line {
    display: flex;
  }

  .validation_line .function {
    font-family: monospace;
    width: 100%;
    display: inline-flex;
    font-size: 0.9rem;
    line-height: 2rem;
  }
</style>
