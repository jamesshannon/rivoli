<script lang="ts">
  import { Anchor, Group, Node, Svelvet, Minimap, Controls } from 'svelvet';

  import type { FileType } from '$lib/rivoli/protos/config_pb';
  import type { Function } from '$lib/rivoli/protos/functions_pb';
  import type { File } from '$lib/rivoli/protos/processing_pb';

  import {
    calculatePlacement,
    makeGraph,
    Node as NodeClass
  } from '$lib/helpers/processing_graph';
  import CreateNode from '../FileProcessingDiagram/CreateNode.svelte';
  import DefaultNode from '../FileProcessingDiagram/DefaultNode.svelte';
  import LoadNode from '../FileProcessingDiagram/LoadNode.svelte';
  import OutputNode from '../FileProcessingDiagram/OutputNode.svelte';
  import ParseNode from '../FileProcessingDiagram/ParseNode.svelte';
  import UploadNode from '../FileProcessingDiagram/UploadNode.svelte';
  import ValidateNode from '../FileProcessingDiagram/ValidateNode.svelte';

  export let file: File;
  export let filetype: FileType;
  export let functions: Map<string, Function>;
  export let visiblePromise: Promise<boolean>;

  const customNodes = {
    CreateNode,
    DefaultNode,
    LoadNode,
    OutputNode,
    ParseNode,
    UploadNode,
    ValidateNode
  };

  let ns = makeGraph(filetype, functions);
  let prom = calculatePlacement(ns);
  //[nodes, groupPosTuple]
</script>

<div class="local">
  {#await visiblePromise then _}
    {#await prom then [nodes, groupPosTuple]}
      <!-- {JSON.stringify(Array.from(nodes.values()))} -->
      <Svelvet id="xyz" TD zoom={0.6} locked>
        <!-- Non-validation Nodes -->
        {#each [...nodes.values()] as node}
          {#if !node.isValidation}
            <svelte:component
              this={customNodes[node.svelteComponentName]}
              {node}
              {file}
            />
          {/if}
        {/each}

        <!-- Validation Nodes -->
        <Group
          color="#0000FF33"
          groupName="validation"
          position={groupPosTuple[0]}
          {...groupPosTuple[1]}
        >
          {#each [...nodes.values()] as node}
            {#if node.isValidation}
              <svelte:component
                this={customNodes[node.svelteComponentName]}
                {node}
                {file}
              />
            {/if}
          {/each}
        </Group>
      </Svelvet>
    {/await}
  {/await}
</div>

<style>
  .local {
    min-height: 500px;
    height: 100%;
  }
  .local :global(div.default-label) {
    font-size: 1.4rem;
  }
</style>
