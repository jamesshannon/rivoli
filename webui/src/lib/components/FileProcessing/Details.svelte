<script lang="ts">
  import { Grid, Row, Column } from 'carbon-components-svelte';

  import type { File } from '$lib/rivoli/protos/processing_pb';

  import { fmtNum } from '$lib/helpers/utils';

  import Progress from '$lib/components/FileProcessing/Progress.svelte';
  import PrettyJson from '$lib/components/PrettyJson.svelte';

  export let file: File;

  function bufferToHex(buffer) {
    return [...new Uint8Array(buffer)]
      .map((b) => b.toString(16).padStart(2, '0'))
      .join('');
  }
</script>

<div class="file_details">
  <Progress {file} />
  <Grid>
    <Row>
      <Column>
        <h5>Size</h5>
        {fmtNum(file.sizeBytes / 1000n)} KB
      </Column>
      <Column>
        <h5>MD5 Hash</h5>
        {bufferToHex(file.hash)}
      </Column>
    </Row>
    <Row>
      <Column>
        <h5>Parameters</h5>
        <PrettyJson json={file.tags} />
      </Column>
      <Column>
        {#if file.headerColumns}
          <h5>Detected Header Columns</h5>
          {file.headerColumns.join(', ')}
        {/if}
      </Column>
    </Row>
  </Grid>
</div>

<style>
  .file_details {
    display: flex;
    margin: 30px 0;
    justify-content: space-between;
  }

  .file_details > :global(.bx--grid) {
    flex-grow: 1;
  }

  .file_details :global(.bx--grid) {
    margin: 0 0 0 80px;
    padding: 0;
  }

  .file_details :global(.bx--row) {
    margin-bottom: 3rem;
  }

  .file_details :global(.bx--col) {
    width: 50%;
  }
</style>
