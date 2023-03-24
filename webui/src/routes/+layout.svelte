<script lang="ts">
	import "carbon-components-svelte/css/g10.css";

	import Header from './Header.svelte';
</script>

<div class="app">
	<link rel='stylesheet' href='%sveltekit.assets%/global.css'>
	<Header />

	<main>
		<slot />
	</main>

	<footer>
		<p>visit <a href="https://kit.svelte.dev">kit.svelte.dev</a> to learn SvelteKit</p>
	</footer>
</div>

<style>
	.app {
		display: flex;
		flex-direction: column;
		min-height: 100vh;
	}

	main {
		flex: 1;
		display: flex;
		flex-direction: column;
		padding: 1rem;
		width: 100%;
		max-width: 64rem;
		margin: 0 auto;
		box-sizing: border-box;
	}

	footer {
		display: flex;
		flex-direction: column;
		justify-content: center;
		align-items: center;
		padding: 12px;
	}

	footer a {
		font-weight: bold;
	}

	:global(.bx--form .bx--label) {
		font-size: 1rem;
	}

  :global(.bx--form .bx--row) {
		margin-bottom: 32px;
	}

	:global(.bx--form .bx--accordion__content) {
		padding-right: 16px;
	}

	@media (min-width: 480px) {
		footer {
			padding: 12px 0;
		}
	}
</style>
