<script lang="ts">
  import { createEventDispatcher } from 'svelte';

  import {
    Checkbox,
    ComboBox,
    FileUploaderDropContainer,
    InlineLoading,
    Modal
  } from 'carbon-components-svelte';

  import type { Partner } from '$lib/rivoli/protos/config_pb';

  export let partnerMap: Map<string, Partner>;
  export let modalOpen: boolean;

  const dispatch = createEventDispatcher();

  let dropLabelText = 'Drag and drop files here or click to upload';
  let fileFS: File;
  let requireNameMatch = true;

  let numEnabled = 0;
  let selectedFtId: string | undefined;

  const filetypeDropdownItems = Array.from(partnerMap.values()).flatMap((p) =>
    p.fileTypes.map((ft) => ({
      id: ft.id,
      partnerId: p.id,
      text: `${p.name} - ${ft.name}`,
      partnerName: p.name,
      filetypeName: ft.name,
      fileMatches: ft.fileMatches,
      // The expression must match the entire filename. Python uses fullmatch();
      // JS doesn't have an equivalent function
      fileMatcheREs: ft.fileMatches.map(
        (nameExp) => new RegExp(`^${nameExp}$`)
      ),
      disabled: false
    }))
  );

  const filetypePartnerMap = new Map(
    filetypeDropdownItems.map((ft) => [ft.id, ft.partnerId])
  );

  function disableDropdownItemsOnFilename(file: File, requireMatch: boolean) {
    numEnabled = 0;

    filetypeDropdownItems.forEach((i) => {
      if (!file || !requireMatch) {
        i.disabled = false;
      } else {
        i.disabled = !i.fileMatcheREs.find((re) => re.test(file.name));
      }

      numEnabled += i.disabled ? 0 : 1;
    });

    console.log('updated disable', filetypeDropdownItems, numEnabled);
  }

  function fileDropHandler(evt: CustomEvent) {
    // Reading through (a potentially large) file locally isn't trivial but is
    // possible. E.g. https://stackoverflow.com/questions/14438187/javascript-filereader-parsing-long-file-in-chunks
    if (evt.detail?.length) {
      fileFS = evt.detail[0] as File;
      dropLabelText = fileFS.name;
    }
  }

  function submitHandler(evt: CustomEvent) {
    if (selectedFtId) {
      dispatch('upload', {
        fileFS,
        filetypeId: selectedFtId,
        partnerId: filetypePartnerMap.get(selectedFtId)
      });
    }
  }

  $: disableDropdownItemsOnFilename(fileFS, requireNameMatch);
</script>

<div class="local">
  <Modal
    bind:open={modalOpen}
    modalHeading="Upload File"
    shouldSubmitOnEnter={false}
    primaryButtonText="Upload"
    on:submit={submitHandler}
  >
    <FileUploaderDropContainer
      labelText={dropLabelText}
      on:change={fileDropHandler}
    />
    <Checkbox
      labelText="Require file name match"
      bind:checked={requireNameMatch}
      disabled={true}
    />

    <ComboBox
      titleText="File Type"
      invalid={numEnabled == 0}
      invalidText="No File Type file match expressions match the uploaded filename."
      items={filetypeDropdownItems}
      bind:selectedId={selectedFtId}
    />
  </Modal>
</div>

<style>
  .local :global(.bx--file__drop-container) {
    height: 3rem;
  }

  /* Copied from function editor */
  :global(.bx--modal-content) {
    overflow-y: visible;
    /* min-height: 180px; */
  }

  :global(.bx--list-box--expanded .bx--list-box__menu) {
    max-height: 20rem;
  }

  :global(.bx--list-box__menu-item) {
    height: 3rem;
  }

  :global(.bx--list-box__menu-item__option) {
    padding-top: 0.5rem;
    height: 3rem;
  }
</style>
