<script lang="ts">
	import { createEventDispatcher, getContext } from 'svelte';

	import { ComboBox, Grid, Row, Column, Modal, TextInput } from 'carbon-components-svelte';

	import { FunctionConfig } from '$lib/protos/config_pb';
	import {
		type Function,
		Function_DataType,
		Function_FunctionType
	} from '$lib/protos/functions_pb';

	import { makeObjectId } from '$lib/helpers/utils';

	export let functionType: Function_FunctionType | Array<Function_FunctionType>;
	export let functionConfig: FunctionConfig | undefined;
	export let open = false;

	let functionsMap: Map<string, Function> = getContext('FUNCTIONS');

	// Allow functionType to be passed as a single value or an array. Coerce it
	// into an array here
	if (!Array.isArray(functionType)) {
		functionType = [functionType];
	}

	let funcConfig: FunctionConfig;
	let func: Function | undefined;

	let selectedId: string | undefined;
	let lastSelectedId: string;

	const dispatch = createEventDispatcher();

	function saveChanges() {
		// Dispatch the functionConfig upward, but only if it's been set up in the
		// modal, which is roughly equivalent to being picked in the dropdown.
		if (funcConfig.functionId) {
			console.log('updating', funcConfig);
			dispatch('save', { functionConfig: funcConfig });
		} else {
			dispatch('save', { functionConfig: null });
		}

		open = false;
	}

	// either get a functionConfig or not.
	// if functionConfig then
	function openHandler() {
		if (functionConfig) {
			funcConfig = functionConfig.clone();
		} else {
			console.log('creating new functionconfig');
			funcConfig = new FunctionConfig({
				id: makeObjectId()
			});
		}

		selectedId = funcConfig.functionId || undefined;
		updateEditor(true);
	}

	function updateEditor(force: boolean = false, _: string | null = null) {
		if (open) {
			if (force || (funcConfig.functionId || '') != (selectedId || '')) {
				funcConfig.functionId = selectedId || '';

				// set the func variable, which the left-hand display is bound to
				if (selectedId) {
					func = functionsMap.get(selectedId);
					funcConfig.parameters = func!.parameters.map(() => '');
				} else {
					func = undefined;
					funcConfig.parameters = [];
				}
			}

			console.log('config id', funcConfig?.id);
		}
	}

	// Combobox - On Change, including first load
	// NB: The on:select handler doesn't get called on *un*select
	$: {
		updateEditor(false, selectedId);
	}

	function shouldFilterItem(item, value) {
		// This should skip all filtering (always return false) when the selected
		// item is chosen and the text exactly matches that item. this could be
		// done by setting selectedItem outside of this function then
		// checking against value == selectedItem.description
		if (!value) return true;
		return (
			item.text.toLowerCase().includes(value.toLowerCase()) ||
			item.description.toLowerCase().includes(value.toLowerCase())
		);
	}

	// Create an array of Combobox-friendly object-ized Functions of *just* the
	// Functions of the correct type
	const items = Array.from(functionsMap.values())
		.filter((f) => (functionType as Array<Function_FunctionType>).includes(f.type))
		.map((f) => ({ id: f.id, text: f.name, description: f.description }));
</script>

<Modal
	on:open={openHandler}
	bind:open
	modalHeading="Edit Function"
	size="lg"
	preventCloseOnClickOutside
	shouldSubmitOnEnter={false}
	primaryButtonText="Save"
	on:click:button--primary={saveChanges}
	secondaryButtonText="Cancel"
	on:click:button--secondary={() => (open = false)}
>
	<div class="local">
		<Grid>
			<Row>
				<Column>
					<ComboBox {items} {shouldFilterItem} bind:selectedId let:item>
						<div>
							<strong><code>{item.text}</code></strong>
						</div>
						<div>
							{item.description}
						</div>
					</ComboBox>
				</Column>
				<Column />
			</Row>
			{#if func}
				<Row class="config_row">
					<Column>
						<div class="function_name">{func.name}(value)</div>
					</Column>
				</Row>

				<Row class="config_row">
					<Column>
						<p class="description">{func.description}</p>

						{#if func.parameters.length}
							<h4>Parameters</h4>
							<ol>
								{#each func.parameters as param}
									<li>
										<code>
											{param.variableName}:
											{Function_DataType[param.type]}
											{#if param.defaultValue} = {param.defaultValue}{/if}
										</code>
										{#if param.description}<p>{param.description}</p>{/if}
									</li>
								{/each}
							</ol>
						{/if}
					</Column>
					<Column>
						{#if func.parameters.length && funcConfig}
							{#each funcConfig.parameters as value}
								<TextInput bind:value />
							{/each}
						{:else}
							<p>
								There is no configuration required as this function doens't take any parameters.
							</p>
						{/if}
					</Column>
				</Row>
			{/if}
		</Grid>
	</div>
</Modal>

<style>
	:global(.bx--modal-content) {
		overflow-y: visible;
		min-height: 180px;
	}

	:global(.bx--list-box--expanded .bx--list-box__menu) {
		max-height: 20rem;
	}

	:global(.bx--list-box__menu-item) {
		height: 3rem;
	}

	:global(.bx--list-box__menu-item__option) {
		padding-top: 0.5rem;
		height: 3rem;
	}

	.local :global(.config_row div.function_name) {
		font-size: 1.5rem;
		font-family: monospace;
	}

	.local :global(.config_row p) {
		padding-right: 0;
		font-size: 1rem;
	}

	.local :global(ol) {
		list-style: inside decimal;
	}
</style>
