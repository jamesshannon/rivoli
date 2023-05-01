<script lang="ts">
  import { getContext } from 'svelte';

  import { Button } from 'carbon-components-svelte';

  import Add from 'carbon-icons-svelte/lib/Add.svelte';
  import Delete from 'carbon-pictograms-svelte/lib/Delete.svelte';
  import Edit from 'carbon-icons-svelte/lib/Edit.svelte';

  import { FunctionConfig } from '$lib/rivoli/protos/config_pb';
  import {
    type Function,
    Function_DataType,
    Function_FunctionType
  } from '$lib/rivoli/protos/functions_pb';
  import FunctionEditorModal from './FunctionEditorModal.svelte';

  // export let fieldtype: FieldType;
  // export let filetype: FileType;

  export let functionConfigs: Array<FunctionConfig>;
  export let functionType: Function_FunctionType;

  let functionsMap: Map<string, Function> = getContext('FUNCTIONS');

  let modalOpen = false;

  let tmpFuncConfig: FunctionConfig | undefined;

  function addNew(evt: MouseEvent) {
    tmpFuncConfig = undefined;
    modalOpen = true;
  }

  function _findFunctionConfig(id: string) {
    return functionConfigs.findIndex((fc) => fc.id == id);
  }

  function editFunction(id: string) {
    // Does this pass by reference and cause problems if "Cancel" is used?
    tmpFuncConfig = functionConfigs[_findFunctionConfig(id)];
    modalOpen = true;
  }

  function deleteFunction(id: string) {
    functionConfigs.splice(_findFunctionConfig(id), 1);
    functionConfigs = functionConfigs;
  }

  function saveChanges(evt) {
    const funcConfig = evt.detail.functionConfig;
    if (!funcConfig) {
      return;
    }

    const existingIdx = functionConfigs.findIndex(
      (fc) => fc.id === funcConfig.id
    );
    if (existingIdx >= 0) {
      functionConfigs[existingIdx] = funcConfig;
    } else if (funcConfig.functionId) {
      // Add a new FunctionConfig based on result from the modal
      functionConfigs.push(funcConfig);
    }
    functionConfigs = functionConfigs;
  }
</script>

<div>
  <ol>
    {#each functionConfigs as functionConfig (functionConfig.id)}
      <li class="validation_line">
        <div class="function">
          {functionsMap.get(functionConfig.functionId)
            ?.name}({functionConfig.parameters.join(', ')})
        </div>
        <Button
          size="small"
          kind="tertiary"
          on:click={() => editFunction(functionConfig.id)}
          iconDescription="Edit"
          icon={Edit}
        />
        <Button
          size="small"
          kind="tertiary"
          on:click={() => deleteFunction(functionConfig.id)}
          iconDescription="Remove"
          icon={Delete}
        />
      </li>
    {/each}
  </ol>
  <Button kind="tertiary" size="small" on:click={addNew} icon={Add}>Add</Button>
</div>

<FunctionEditorModal
  on:save={saveChanges}
  bind:open={modalOpen}
  functionConfig={tmpFuncConfig}
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

  .validation_line :global(.bx--btn--sm.bx--btn--icon-only) {
    height: 32px;
  }
</style>
