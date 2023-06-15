<script lang="ts">
import {
  Button,
  TextInput,
  FormGroup,
} from "carbon-components-svelte";
import Add from "carbon-icons-svelte/lib/Add.svelte";
import Delete from "carbon-pictograms-svelte/lib/Delete.svelte";


export let strings: Array<string> = [];

function addString() {
  strings.push('');
  strings = strings;
}

function removeString(idx: number) {
  strings.splice(idx, 1);
  strings = strings;
}

</script>

<div class="local">
  {#each strings as str, idx}
    <FormGroup class="string-list">
      <TextInput bind:value="{str}" />
      <Button
       kind="tertiary"
       expressive
       on:click={() => removeString(idx)}
       iconDescription="Remove"
       icon={Delete} />
    </FormGroup>
  {:else}
    <div>There are no items</div>
  {/each}
  <Button
   size="small"
   kind="tertiary"
   icon={Add}
   on:click={addString}>Add</Button>
</div>


<style>
  .local :global(.string-list) {
    display: flex;
    justify-content: space-between;
  }

  .local :global(.string-mapping *) {
    display: inline-flex;
  }

  .local :global(.value) {
    margin-right: 20px;
  }

  .local :global(.string-list .bx--btn) {
    min-height: 0;
    padding: 1px 6px;
  }

  .local :global(.bx--fieldset) {
    margin-bottom: 8px;
  }

</style>

