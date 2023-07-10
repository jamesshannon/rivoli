<script lang="ts">
  import {
    FormGroup,
		TextInput,
    Button,
  } from "carbon-components-svelte";
  import Add from "carbon-icons-svelte/lib/Add.svelte";
  import Delete from "carbon-pictograms-svelte/lib/Delete.svelte";

  export let staticTags: {[key: string]: string} = {};

  // This componnent operates on an array of key:value tuples, but updates
  // the bound object on any changes
  let tagEntries = Object.entries(staticTags);

  $: staticTags = Object.fromEntries(tagEntries);

  function addItem() {
    tagEntries.push(['', '']);
    tagEntries = tagEntries;
  }

  function removeItem(idx: number) {
    tagEntries.splice(idx, 1);
    tagEntries = tagEntries;
  }
</script>

<div class="local">
  <FormGroup>

    {#each tagEntries as [key, value], idx}
      <FormGroup class="string-mapping">
        <div class="key">
          <TextInput bind:value={key} />
        </div>
        <span class="separator">=</span>
        <div class="value">
          <TextInput bind:value={value} />
        </div>
        <Button
         kind="tertiary"
         expressive
         on:click="{() => removeItem(idx)}"
         iconDescription="Remove"
         icon={Delete} />
      </FormGroup>
    {:else}
      <p>There are no items</p>
    {/each}

    <Button
     size="small"
     kind="tertiary"
     icon={Add}
     on:click={addItem}>Add</Button>

  </FormGroup>
</div>


<style>
  .local :global(.string-mapping) {
    display: flex;
    justify-content: space-between;
  }

  .local :global(.string-mapping > *) {
    display: inline-flex;
  }

  .local :global(.string-mapping .key) {
    flex-grow: 1;
  }

  .separator {
    font-size: 300%;
    font-weight: bold;
    margin: -5px 5px 0 5px;
  }

  .local :global(.string-mapping .value) {
    flex-grow: 5;
    margin-right: 15px;
  }

  .local :global(.string-mapping .bx--btn) {
    min-height: 0;
    padding: 1px 6px;
  }

  .local :global(.bx--fieldset) {
    margin-bottom: 8px;
  }

</style>
