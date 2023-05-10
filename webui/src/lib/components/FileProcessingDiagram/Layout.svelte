<script lang="ts">
  import { truncate } from 'carbon-components-svelte';
  import type { CarbonIcon } from 'carbon-icons-svelte';
  import type { SvelteComponent } from 'svelte';

  export let icon: SvelteComponent | undefined = undefined;
  export let titleText = '';
  export let description = '';
</script>

<div class="node_layout">
  <h4>
    {#if icon}<svelte:component this={icon} size={32} />{/if}
    <span title={titleText}>{titleText}</span>
  </h4>
  <div class="desc">{description}</div>
  <div><slot /></div>
</div>

<style>
  .node_layout {
    max-width: 100%;
  }

  h4 {
    display: flex;
    width: 100%;
    align-items: center;
  }

  h4 :global(svg) {
    flex: 1 0 auto;
    margin-right: 8px;
  }

  h4 span {
    font-size: 1.8rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  div.desc {
    font-size: 1.3rem;
  }
</style>
