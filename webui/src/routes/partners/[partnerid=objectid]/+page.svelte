<script lang="ts">
  import type { PageData } from './$types';

  import {
    Breadcrumb,
    BreadcrumbItem,
    Button,
    DataTable,
    InlineNotification,
    Link,
    Toolbar,
    ToolbarContent,
    ToolbarSearch
  } from 'carbon-components-svelte';
  import Add from 'carbon-icons-svelte/lib/Add.svelte';

  import PartnerForm from '$lib/components/PartnerForm/PartnerForm.svelte';

  import { Partner } from '$lib/rivoli/protos/config_pb';

  import type { JsonValue } from '@bufbuild/protobuf';

  export let data: PageData;
  let partner = Partner.fromJson(data.partner as any as JsonValue);

  let fileTypeHeader = [{ key: 'name', value: 'File Type' }];
  let fileTypeRows = partner.fileTypes.map((f) => ({ id: f.id, name: f.name }));

  let submitHandler = async function (evt: CustomEvent) {
    let partner = evt.detail.partner as Partner;
    const respbody = await (
      await fetch('/partners', { method: 'POST', body: partner.toJsonString() })
    ).json();

    console.log('how come active=false doent save?');
    console.log('show success and error message. Maybe in a form library?');
    console.log(respbody);
  };
</script>

<svelte:head>
  <title>Edit Partner</title>
</svelte:head>

<h1>{partner.name}</h1>
<Breadcrumb noTrailingSlash>
  <BreadcrumbItem href="/">Home</BreadcrumbItem>
  <BreadcrumbItem href="/partners">Partners</BreadcrumbItem>
  <BreadcrumbItem isCurrentPage>Edit</BreadcrumbItem>
</Breadcrumb>

<div id="notification">
  <InlineNotification
    kind="success"
    title="Success:"
    subtitle="Partner record saved"
    timeout={3000}
  />
</div>

<PartnerForm bind:partner on:submit={submitHandler} />

<h2>File Types</h2>

<DataTable headers={fileTypeHeader} rows={fileTypeRows}>
  <Toolbar>
    <ToolbarContent>
      <ToolbarSearch persistent shouldFilterRows />
      <Link href="/partners/{partner.id}/filetypes/new"
        ><Button
          kind="secondary"
          iconDescription="Add New File Type"
          icon={Add}
        /></Link
      >
    </ToolbarContent>
  </Toolbar>
  <svelte:fragment slot="cell" let:row let:cell>
    {#if cell.key === 'name'}
      <Link href="/partners/{partner.id}/filetypes/{row.id}">{cell.value}</Link>
    {:else}
      {cell.value}
    {/if}
  </svelte:fragment>
</DataTable>

<style>
  #notification {
    display: block;
    width: 100%;
    position: fixed;
    top: 0;
    z-index: 1000;
  }
</style>
