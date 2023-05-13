<script lang="ts">
  import { DocumentAdd } from 'carbon-icons-svelte';

  import type { Node as NodeClass } from '$lib/helpers/processing_graph';
  import type { File } from '$lib/rivoli/protos/processing_pb';

  import DefaultNode from '$lib/components/FileProcessingDiagram/DefaultNode.svelte';
  import Layout from '$lib/components/FileProcessingDiagram/Layout.svelte';

  export let node: NodeClass;
  export let file: File | undefined = undefined;
</script>

<DefaultNode {node} showInputAnchors={false} status="COMPLETE">
  <Layout icon={DocumentAdd} titleText={node.name} description="Create File">
    {#if file && file.stats?.approximateRows}
      ~{file.stats?.approximateRows} lines
    {/if}
  </Layout>
</DefaultNode>
