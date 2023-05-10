<script lang="ts">
  import { Anchor, Node as SvelteNode } from 'svelvet';

  import type { Node as NodeClass } from '$lib/helpers/processing_graph';
  import {
    CheckmarkFilled,
    CheckmarkFilledError,
    Renew
  } from 'carbon-icons-svelte';

  //export let position = { x: 0, y: 0 };
  export let node: NodeClass;

  export let showInputAnchors = true;
  export let showOutputAnchors = true;

  export let file: File = null;

  export let inputCount = '';
  export let status = '';

  export let width = 300;
  export let height = 150;

  const statusIcons = new Map([
    ['PROCESSING', Renew],
    ['ERROR', CheckmarkFilledError],
    ['COMPLETE', CheckmarkFilled]
  ]);
</script>

<SvelteNode id={node.id} position={node.position}>
  {#if statusIcons.get(status)}
    <div class="check {status}">
      <svelte:component this={statusIcons.get(status)} size={32} />
    </div>
  {/if}
  <div class="node-body {status}" style="width: {width}px; height: {height}px;">
    {#if !$$slots.default}
      {node.name}
    {/if}
    <slot />
  </div>
  {#if showInputAnchors}
    <div class="input-anchors">
      <Anchor
        id={`${node.id}-input`}
        input
        direction="north"
        edgeLabel={inputCount}
        connections={node.getInputIDs().map((nid) => [nid, `${nid}-output`])}
      />
    </div>
  {/if}
  {#if showOutputAnchors}
    <div class="output-anchors">
      <Anchor id={`${node.id}-output`} output direction="south" />
    </div>
  {/if}
</SvelteNode>

<style>
  .check {
    position: absolute;
    left: -16px;
    top: -16px;
    color: blue;
  }

  .check.ERROR {
    color: red;
  }

  .check.COMPLETE {
    color: green;
  }

  .check.PROCESSING {
    animation: spin 4s linear infinite;
  }

  .node-body {
    display: flex;
    background-color: lightcyan;
    padding: 10px;
    flex-direction: column;
    align-items: flex-start;
  }

  .input-anchors {
    position: absolute;
    display: flex;
    flex-direction: column;
    gap: 10px;
    top: -8px;
  }

  .output-anchors {
    position: absolute;
    bottom: -8px;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  @keyframes spin {
    100% {
      -webkit-transform: rotate(360deg);
      transform: rotate(360deg);
    }
  }
</style>
