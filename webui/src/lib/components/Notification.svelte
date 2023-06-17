<script lang="ts">
  import { ToastNotification } from "carbon-components-svelte";

  let visible = false;
  let kind = 'info';
  let title = '';
  let subtitle = '';

  export function showNotification(response: {[key: string]: any}) {
    kind = response.status;

    if (kind === 'success') {
      title = 'Success!';
    } else if (kind === 'error') {
      title = 'Error'
    }
    subtitle = response.data.message;

    visible = true;

    window.setTimeout(() => {
      visible = false;
    }, 5000);
  }
</script>

<div class="local" class:visible="{visible}">
  {#if visible}
    <ToastNotification kind={kind} >
      <strong slot="title">{title}</strong>
      <strong slot="subtitle">{subtitle}</strong>
    </ToastNotification>
  {/if}
</div>

<style>
  div.local {
    position: absolute;
    transition: 0.5s;
    z-index: 100;
    right: -500px;
    margin-top: -25px;
  }

  div.local.visible {
    right: 0;
  }
</style>
