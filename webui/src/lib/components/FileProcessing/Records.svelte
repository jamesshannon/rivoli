<script lang="ts">
  import { Button, Dropdown, Modal } from 'carbon-components-svelte';

  import type { FileType } from '$lib/rivoli/protos/config_pb';
  import { Record_Status, type File } from '$lib/rivoli/protos/processing_pb';
  import type { RecordsFilter } from '$lib/helpers/file_processing/records';

  export let file: File;
  export let filetype: FileType;

  export let statusCounts: Map<string, number>;
  export let filter: RecordsFilter;

  const recordTypes = new Map(filetype.recordTypes.map((rt) => [rt.id, rt]));

  let revertModalOpen = false;
  let revertModalEnabled = false;

  let statusDropdownOptions: Array<any>;
  $: statusDropdownOptions = [{ id: '', text: 'All Statuses' }].concat(
    Array.from(statusCounts).map(([status, cnt]) => ({
      id: status,
      text: `${Record_Status[status]} (${cnt})`
    }))
  );

  function filterStatusSelected() {
    // binding the property to the Dropdown doesn't cause filter reactivity to
    // work as expected
    filter = filter;
  }
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
    Revert {filteredResultCount} records to <Dropdown
      size="sm"
      type="inline"
      items={revertToDropdownOptions}
      selectedId={revertToId}
    />?
    <p>
      Reverting the record status will cause these {filteredResultCount} records
      and the file status to be reset.
    </p>
  </Modal>
</div>
