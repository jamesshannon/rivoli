<script lang="ts">
  import { goto, invalidate } from '$app/navigation';

  import { Breadcrumb, BreadcrumbItem } from 'carbon-components-svelte';

  import PartnerForm from '$lib/components/PartnerForm/PartnerForm.svelte';

  import type { Partner } from '$lib/rivoli/protos/config_pb';

  let submitHandler = async function (evt: CustomEvent) {
    let partner = evt.detail.partner as Partner;
    const respbody = await (
      await fetch('/partners', { method: 'POST', body: partner.toJsonString() })
    ).json();

    goto(`/partners/${respbody.partner.id}`);
  };
</script>

<Breadcrumb noTrailingSlash>
  <BreadcrumbItem href="/">Home</BreadcrumbItem>
  <BreadcrumbItem href="/partners">Partners</BreadcrumbItem>
  <BreadcrumbItem href="/partners/new" isCurrentPage>New Partner</BreadcrumbItem
  >
</Breadcrumb>

<PartnerForm on:submit={submitHandler} />
