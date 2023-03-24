<script lang="ts">
  import "carbon-components-svelte/css/g10.css";

	import {
		Breadcrumb, BreadcrumbItem,
		Button,
		DataTable,
		Link,
		Toolbar, ToolbarContent, ToolbarSearch
	} from "carbon-components-svelte";
	import Add from "carbon-icons-svelte/lib/Add.svelte";

  import type { PageData } from './$types';

	import { Function, Function_FunctionType } from "$lib/protos/functions_pb";


  export let data: PageData;

  let headers = [
		{key: 'name', value: 'Function'},
    {key: 'type', value: 'Type'},
    {key: 'isSystem', value: 'System'},
	]
	let rows = Array.from (data.functionsMap.values()).map((f) => ({
    id: f.id,
    name: f.name,
    type: Function_FunctionType[f.type],
    isSystem: f.isSystem,
  }));
</script>

<svelte:head>
	<title>Home</title>
	<meta name="description" content="Svelte demo app" />


</svelte:head>

<Breadcrumb noTrailingSlash>
  <BreadcrumbItem href="/">Home</BreadcrumbItem>
  <BreadcrumbItem href="/functions" isCurrentPage>Functions</BreadcrumbItem>
</Breadcrumb>

<DataTable {headers} {rows}>
	<Toolbar>
		<ToolbarContent>
			<ToolbarSearch
        persistent
        shouldFilterRows
      />
			<Link href="/functions/new">
				<Button kind="secondary" iconDescription="Add New Function" icon={Add} />
			</Link>
		</ToolbarContent>
	</Toolbar>
	<svelte:fragment slot="cell" let:row let:cell>
    {#if cell.key === "name"}
      <code><Link href="/functions/{row.id}">{cell.value}()</Link></code>
    {:else}
      {cell.value}
    {/if}
  </svelte:fragment>
</DataTable>

