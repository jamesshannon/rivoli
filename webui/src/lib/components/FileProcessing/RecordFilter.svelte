<script lang="ts">
  import { createEventDispatcher } from 'svelte';

  import { Button, Dropdown, Modal } from 'carbon-components-svelte';

  import type { FileType } from '$lib/rivoli/protos/config_pb';
  import { Record_Status, type File } from '$lib/rivoli/protos/processing_pb';
  import {
    REVERTABLE_MAP,
    type RecordsFilter
  } from '$lib/helpers/file_processing/records';

  interface DropdownItem {
    id: string;
    text: string;
    disabled?: boolean;
  }

  export let file: File;
  export let filetype: FileType;

  export let statusCounts: Map<string, number>;
  export let filter: RecordsFilter;

  const dispatch = createEventDispatcher();

  let revertModalOpen = false;
  let revertModalEnabled = false;

  let statusDropdownOptions: Array<DropdownItem>;

  // Array of statuses which can be reverted to
  let revertToStatuses: Record_Status[] | undefined;
  let revertToDropdownOptions: Array<DropdownItem>;
  let revertToId: string;

  // Update the variables to display the modal based on changes to the
  // filter.status value
  $: revertToStatuses = REVERTABLE_MAP.get(parseInt(filter.status));
  $: revertModalEnabled = !!revertToStatuses;
  $: revertToDropdownOptions = revertToStatuses
    ? revertToStatuses.map((s) => ({
        id: s.toString(),
        text: Record_Status[s]
      }))
    : [];
  // Set the default revertTo dropdown value
  $: revertToId = revertToStatuses
    ? revertToDropdownOptions[revertToDropdownOptions.length - 1].id
    : '';
  $: console.log('reactive dropdown options', revertToDropdownOptions);

  $: statusDropdownOptions = [{ id: '', text: 'All Statuses' }].concat(
    Array.from(statusCounts).map(([status, cnt]) => ({
      id: status,
      text: `${Record_Status[status]} (${cnt})`
    }))
  );

  function filterStatusSelected() {
    dispatch('filtered');
  }

  export function resetFilters() {
    // Reset the filters, reset the UI, and close the modal
    // This is used after records are reverted
    filter.reset();
    filter = filter;
    revertModalOpen = false;
    filterStatusSelected();
  }

  function revertRecordStatuses() {
    //    revertModalEnabled = false;

    if (!revertModalEnabled || !revertToId) {
      // revertModalEnabled is reactive to the dropdown status, so this ensures
      // a valid dropdown status
      return;
    }

    // bubble up a revert, along with revertToId
    dispatch('revert', { filter: filter, revertToId: revertToId });
  }

  $: console.log('rf filter status:', filter.status);
</script>

<div id="filters">
  <Dropdown
    type="inline"
    titleText="Status"
    items={statusDropdownOptions}
    bind:selectedId={filter.status}
    on:select={filterStatusSelected}
  />

  <Button
    size="field"
    kind="tertiary"
    disabled={!revertModalEnabled}
    on:click={() => {
      revertModalOpen = true;
    }}>Revert Record Statuses</Button
  >
</div>

<div class="localmodal">
  <Modal
    bind:open={revertModalOpen}
    modalHeading="Revert Records"
    primaryButtonText="Confirm"
    secondaryButtonText="Cancel"
    on:click:button--primary={revertRecordStatuses}
    on:click:button--secondary={() => (revertModalOpen = false)}
  >
    Revert {filter.resultCount} records to <Dropdown
      size="sm"
      type="inline"
      items={revertToDropdownOptions}
      selectedId={revertToId}
    />?
    <p>
      Reverting the record status will cause these {filter.resultCount} records and
      the file status to be reset.
    </p>
  </Modal>
</div>

<style>
  #filters {
    margin: 10px;
    border: 1px solid blue;
    padding: 10px;
  }

  .localmodal :global(.bx--dropdown__wrapper--inline) {
    position: relative;
    top: -5px;
    grid-gap: 0;
    gap: 0;
  }

  .localmodal :global(.bx--modal-content) {
    overflow-y: visible;
  }
</style>
