<script lang="ts">
  import { page } from '$app/stores';
  import type { PageData } from './$types';

  import {
    Breadcrumb, BreadcrumbItem,
  } from "carbon-components-svelte";

  import { Partner, FileType } from "$lib/protos/config_pb";

  import FileTypeForm from "$lib/components/FileTypeForm.svelte";
  import type { JsonValue } from '@bufbuild/protobuf';

  export let data: PageData;
  let partner = Partner.fromJson(data.partner as any as JsonValue);
  let filetype = partner.fileTypes.find((ft) => ft.id == $page.params.filetypeid)!;

  let submitHandler = async function(evt) {
    try {
      console.log('submitting')
      const res = await client.savePartner({partner: partner});
      console.log(res);
    } catch (err) {
      console.log('got error' , err.name, err.message);
      console.log('full error', err)
    }
  }

</script>

<Breadcrumb noTrailingSlash>
  <BreadcrumbItem href="/">Home</BreadcrumbItem>
  <BreadcrumbItem href="/partners">Partners</BreadcrumbItem>
  <BreadcrumbItem href="/partners/{ partner.id }">{ partner.name }</BreadcrumbItem>
  <BreadcrumbItem href="/partners/{ partner.id }#filetypes">Filetypes</BreadcrumbItem>
  <BreadcrumbItem href="/partners/{ partner.id }/filetypes/{ filetype.id }" isCurrentPage>{ filetype.name }</BreadcrumbItem>
</Breadcrumb>

<FileTypeForm bind:filetype={filetype} functionsMap={data.functionsMap}
    showRecordTypes={true} on:submit={submitHandler} />
