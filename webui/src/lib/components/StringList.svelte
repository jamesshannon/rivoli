<script lang="ts">
import {
  Button,
  TextInput,
  FormGroup,
} from "carbon-components-svelte";
import Delete from "carbon-pictograms-svelte/lib/Delete.svelte";


export let strings: Array<string> = [];
let stringElements = strings;

$: {
  let last_idx = stringElements.length - 1;
  if (last_idx == -1 || stringElements[last_idx]) {
    stringElements.push('');
  }

  // Assign all non-empty strings to the bound strings property
  let newstrings = [];
  for (const str of stringElements) {
    if (str) {
      newstrings.push(str);
    }
  }
  strings = newstrings;
}
</script>

<div class="local">
  {#each stringElements as str}
    <FormGroup class="string-list">
      <TextInput bind:value="{str}" />
      <Button iconDescription="Remove" kind="tertiary" expressive icon={Delete} />
    </FormGroup>
  {/each}
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

  .local :global(.bx--btn) {
    min-height: 0;
    padding: 1px 6px;
  }

  .local :global(.bx--fieldset) {
    margin-bottom: 8px;
  }

</style>

