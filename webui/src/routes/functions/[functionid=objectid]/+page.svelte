<script lang="ts">
  import { Breadcrumb, BreadcrumbItem } from 'carbon-components-svelte';

  import type { PageData } from './$types';

  import FunctionForm from '$lib/components/FunctionForm.svelte';
  import { Function } from '$lib/rivoli/protos/functions_pb';

  export let data: PageData;

  let func = Function.fromJson(data.func as any);

  let submitHandler = async function (evt) {
    const res = await client.saveFunction({ function: evt.detail.function });
  };
</script>

<Breadcrumb noTrailingSlash>
  <BreadcrumbItem href="/">Home</BreadcrumbItem>
  <BreadcrumbItem href="/functions">Functions</BreadcrumbItem>
  <BreadcrumbItem href="/functions/{data.func.id}}" isCurrentPage
    >{data.func.name}</BreadcrumbItem
  >
</Breadcrumb>

<FunctionForm bind:func on:submit={submitHandler} />
