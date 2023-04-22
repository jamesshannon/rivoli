<script lang="ts">
  import { syntaxHighlight } from '$lib/helpers/utils';

  export let json: any;
</script>

<pre class="pretty_json">{@html syntaxHighlight(json)}</pre>

<style>
  .pretty_json :global(.string) {
    color: green;
  }
  .pretty_json :global(.number) {
    color: darkorange;
  }
  .pretty_json :global(.boolean) {
    color: blue;
  }
  .pretty_json :global(.null) {
    color: magenta;
  }
  .pretty_json :global(.key) {
    color: red;
  }
</style>
