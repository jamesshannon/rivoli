<script lang="ts">
	import { goto } from '$app/navigation';
	import type { PageData } from './$types';

	import { Breadcrumb, BreadcrumbItem } from 'carbon-components-svelte';

	import type { JsonValue } from '@bufbuild/protobuf';

	import { Partner, FileType, RecordType } from '$lib/protos/config_pb';

	import { makeObjectId } from '$lib/helpers/utils';

	import FileTypeForm from '$lib/components/FileTypeForm.svelte';

	//import RecordTypeSubForm from "$lib/components/RecordTypeSubForm.svelte";

	export let data: PageData;
	let partner = Partner.fromJson(data.partner as any as JsonValue);
	let filetype = new FileType();
	partner.fileTypes.push(filetype);

	let submitHandler = async function (evt: CustomEvent) {
		let ft = evt.detail.filetype as FileType;
		// This is a sub-document so mongo doesn't return the id
		filetype.id = makeObjectId();
		// Add a default recordtype
		filetype.recordTypes.push(new RecordType({ name: `[${filetype.name} Records]` }));

		const response = await fetch('/partners', { method: 'POST', body: partner.toJsonString() });
		const result = await response.json();
		console.log(partner.fileTypes);

		goto(`/partners/${partner.id}/filetypes/${filetype.id}`);
	};
</script>

<Breadcrumb noTrailingSlash>
	<BreadcrumbItem href="/">Home</BreadcrumbItem>
	<BreadcrumbItem href="/partners">Partners</BreadcrumbItem>
	<BreadcrumbItem href="/partners/{partner.id}">{partner.name}</BreadcrumbItem>
	<BreadcrumbItem href="/partners/{partner.id}#filetypes">Filetypes</BreadcrumbItem>
	<BreadcrumbItem href="/partners/{partner.id}/filetypes/new" isCurrentPage
		>New Filetype</BreadcrumbItem
	>
</Breadcrumb>

<FileTypeForm showRecordTypes={false} bind:filetype on:submit={submitHandler} />
