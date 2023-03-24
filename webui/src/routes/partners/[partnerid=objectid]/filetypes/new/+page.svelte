<script lang="ts">
import "carbon-components-svelte/css/g10.css";
import type { PageData } from './$types';

import {
  Breadcrumb, BreadcrumbItem
} from "carbon-components-svelte";

import { Partner, FileType, RecordType } from "$lib/protos/config_pb";

import {client} from "$lib/grpc";

import { goto } from '$app/navigation';
import FileTypeForm from "$lib/components/FileTypeForm.svelte";
//import RecordTypeSubForm from "$lib/components/RecordTypeSubForm.svelte";

export let data: PageData;
let partner: Partner = data.partner!;
let filetype = new FileType();
partner.fileTypes.push(filetype);

// since bson doesn't work in the browser...
const genRanHex = size => [...Array(size)].map(() => Math.floor(Math.random() * 16).toString(16)).join('')

let submitHandler = async function(evt) {
  // This is a sub-document so mongo doesn't return the id
  filetype.id = genRanHex(24);
  // Add a default recordtype
  filetype.records.push(new RecordType({name: `[${filetype.name} Records]`}));
  const res = await client.savePartner({partner: partner});
  goto(`/partners/${partner.id}/filetypes/${filetype.id}`);
}
</script>


<Breadcrumb noTrailingSlash>
  <BreadcrumbItem href="/">Home</BreadcrumbItem>
  <BreadcrumbItem href="/partners">Partners</BreadcrumbItem>
  <BreadcrumbItem href="/partners/{ partner.id }">{ partner.name }</BreadcrumbItem>
  <BreadcrumbItem href="/partners/{ partner.id }#filetypes">Filetypes</BreadcrumbItem>
  <BreadcrumbItem href="/partners/{ partner.id }/filetypes/new" isCurrentPage>New Filetype</BreadcrumbItem>
</Breadcrumb>

<FileTypeForm showRecordTypes={false} bind:filetype={filetype} on:submit={submitHandler} />
