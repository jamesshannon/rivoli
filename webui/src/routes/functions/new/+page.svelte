<script lang="ts">

	import {
		Breadcrumb, BreadcrumbItem
  } from "carbon-components-svelte";

  import FunctionForm from "$lib/components/FunctionForm.svelte";

  import { goto } from '$app/navigation';

  let submitHandler = async function(evt) {
    const res = await client.saveFunction({'function': evt.detail.function});
    goto(`/functions/${res.function.id}`);
  }
</script>

<Breadcrumb noTrailingSlash>
  <BreadcrumbItem href="/">Home</BreadcrumbItem>
  <BreadcrumbItem href="/functions">Functions</BreadcrumbItem>
  <BreadcrumbItem href="/partners/new" isCurrentPage>New Function</BreadcrumbItem>
</Breadcrumb>

<FunctionForm on:submit={submitHandler}/>
