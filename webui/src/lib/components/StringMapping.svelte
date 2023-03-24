<script lang="ts">
  import {
    FormGroup,
		TextInput,
    Button,
  } from "carbon-components-svelte";

  import Delete from "carbon-pictograms-svelte/lib/Delete.svelte";

  export let staticTags: {[key: string]: string} = {};

  function btnRemove(evt) {
    console.log('removing', evt.target)
  }

  let tagEntries = Object.entries(staticTags);

  $: {
    let last_idx = tagEntries.length - 1;
    if (last_idx == -1 || tagEntries[last_idx][0] || tagEntries[last_idx][1]) {
      tagEntries.push(['', ''])
    }

    // Create a new object from the array and assign back to staticTags
    let newtags: {[key: string]: string} = {};
    // Exclude the last item which is empty
    for (const [key, value] of tagEntries) {
      if (key && value) {
        newtags[key] = value;
      }
    }

    staticTags = newtags;
  }
</script>

<div class="local">
  <FormGroup>

    {#each tagEntries as [key, value]}
      <FormGroup class="string-mapping">
        <TextInput class="key" bind:value={key} id="" />
        <span class="separator">:</span>
        <TextInput class="value" id="2" bind:value={value} />
        <Button on:click="{btnRemove}" iconDescription="Remove" kind="tertiary"
            expressive icon={Delete} />
      </FormGroup>
    {/each}

  </FormGroup>
</div>


<style>
  .local :global(.string-mapping) {
    display: flex;
    justify-content: space-between;
  }

  .local :global(.string-mapping *) {
    display: inline-flex;
  }

  .separator {
    font-size: 300%;
    margin: -5px 15px 0 15px;
  }

  .local :global(.value) {
    margin-right: 15px;
  }

  .local :global(.bx--btn) {
    min-height: 0;
    padding: 1px 6px;
  }

  .local :global(.bx--fieldset) {
    margin-bottom: 8px;
  }

</style>
