<script lang="ts">
	import "carbon-components-svelte/css/g10.css";

	import {
		Breadcrumb, BreadcrumbItem
  } from "carbon-components-svelte";

  import type { PageData } from './$types';

  import FunctionForm from "$lib/components/FunctionForm.svelte";

  import { client } from "$lib/grpc";
  import { goto } from '$app/navigation';

  export let data: PageData;

  let submitHandler = async function(evt) {
    const res = await client.saveFunction({'function': evt.detail.function});
  }
  console.log(data.func);
</script>

<Breadcrumb noTrailingSlash>
  <BreadcrumbItem href="/">Home</BreadcrumbItem>
  <BreadcrumbItem href="/functions">Functions</BreadcrumbItem>
  <BreadcrumbItem href="/functions/{data.func.id}}" isCurrentPage>{data.func.name}</BreadcrumbItem>
</Breadcrumb>

<FunctionForm bind:func={data.func} on:submit={submitHandler}/>
