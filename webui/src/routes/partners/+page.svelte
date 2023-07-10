<script lang="ts">
	import type { PageData } from './$types';

	import {
		Breadcrumb, BreadcrumbItem,
		Button,
		DataTable,
		Link,
		Toolbar, ToolbarContent, ToolbarSearch
	} from "carbon-components-svelte";

	import Add from "carbon-icons-svelte/lib/Add.svelte";


  export let data: PageData;

  let headers = [
		{key: 'name', value: 'Partner'},
		{key: 'fileTypes', value: 'File Types'},
	]
  let rows = Array.from(data.partners.values())
	    .map((p) => ({
				id: p.id,
				name: p.name,
				fileTypes: p.fileTypes,
			}));
</script>

<svelte:head>
	<title>Rivoli - Partners</title>
</svelte:head>

<Breadcrumb noTrailingSlash>
  <BreadcrumbItem href="/">Home</BreadcrumbItem>
  <BreadcrumbItem href="/partners" isCurrentPage>Partners</BreadcrumbItem>
</Breadcrumb>

<DataTable {headers} {rows}>
	<Toolbar>
		<ToolbarContent>
			<ToolbarSearch persistent shouldFilterRows />
			<Link href="/partners/new">
				<Button kind="secondary" iconDescription="Add New Partner" icon={Add} />
			</Link>
		</ToolbarContent>
	</Toolbar>
	<svelte:fragment slot="cell" let:row let:cell>
    {#if cell.key === "name"}
      <Link href="/partners/{row.id}">{cell.value}</Link>
		{:else if cell.key === "fileTypes"}
			{#each cell.value as ft, idx}
				<a href="/partners/{row.id}/filetypes/{ft.id}">
					{ft.name}</a>{#if idx < cell.value.length - 1},&nbsp;{/if}
			{/each}
    {:else}
      {cell.value}
    {/if}
  </svelte:fragment>
</DataTable>

