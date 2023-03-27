<script lang="ts">
	import "carbon-components-svelte/css/g10.css";

	import { Content, Header, HeaderNav, HeaderNavItem } from "carbon-components-svelte";
	import { Grid, Row, Column } from "carbon-components-svelte";

	import Logo from '$lib/assets/Logo.svelte';
</script>

<div class="app">
	<link rel='stylesheet' href='%sveltekit.assets%/global.css'>
	<Header platformName="Rivoli">
		<svelte:fragment slot="platform">
			<Logo color="white" class="header_logo"/>  Rivoli
		</svelte:fragment>
		<HeaderNav>
			<HeaderNavItem href="/files" text="Files" />
			<HeaderNavItem href="/partners" text="Partners" />
			<HeaderNavItem href="/functions" text="Functions" />
		</HeaderNav>
	</Header>

	<Content>
		<Grid>
			<Row>
				<Column>
					<slot />
				</Column>
			</Row>
		</Grid>
	</Content>

	<footer>
		...
	</footer>
</div>

<style>
<<<<<<< HEAD
	:global(.header_logo) {
		height: 100%;
		padding: 10% 10% 10% 0;
=======
	.header_logo {
		height: 100%;
>>>>>>> main
	}

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
