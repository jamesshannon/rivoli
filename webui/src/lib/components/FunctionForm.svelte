<script lang="ts">
	import { createEventDispatcher } from 'svelte';

	import {
		Form,
		FormLabel,
		Checkbox,
		Dropdown,
		Grid,
		Row,
		Column,
		TextInput,
		Button,
		TextArea
	} from 'carbon-components-svelte';

	import { Function, Function_FunctionType } from '$lib/protos/functions_pb';

	export let func: Function | undefined = undefined;
	export let readonly: boolean = false;

	const dispatch = createEventDispatcher();

	if (!func) {
		func = new Function({
			type: Function_FunctionType.FIELD_VALIDATION,
			functionStatement: { case: 'sqlCode' }
		});
	}

	readonly = readonly || func.isSystem;

	const functionTypeDropdownItems = [
		{ id: Function_FunctionType.FIELD_VALIDATION, text: 'Field - Modify or Validate' },
		{ id: Function_FunctionType.RECORD_VALIDATION, text: 'Record - Modify or Validate' },
		{ id: Function_FunctionType.RECORD_UPLOAD, text: 'Upload Record' },
		{ id: Function_FunctionType.RECORD_UPLOAD_BATCH, text: 'Upload Batch Records' }
	];

	const statementDropdownAllItems = [
		{ id: 'pythonFunction', text: 'Python Function' },
		{ id: 'sqlCode', text: 'SQL Statement' }
	];

	function submitHandler() {
		dispatch('submit', { function: func });
	}
</script>

<div class="local">
	<Form on:submit={submitHandler}>
		<Grid>
			<Row>
				<Column
					><TextInput
						labelText="Function Name"
						disabled={readonly}
						bind:value={func.name}
					/></Column
				>
				<Column
					><Checkbox labelText="Active" disabled={readonly} bind:checked={func.active} /></Column
				>
			</Row>
			<Row>
				<Column>
					<TextArea labelText="Documentation" disabled={readonly} bind:value={func.description} />
				</Column>
			</Row>

			<Row>
				<Column>
					<Dropdown
						titleText="Function Type"
						disabled={readonly}
						bind:selectedId={func.type}
						items={functionTypeDropdownItems}
					/>
				</Column>
				<Column>
					<Dropdown
						titleText="Function Code or Pointer"
						disabled={readonly}
						bind:selectedId={func.functionStatement.case}
						items={statementDropdownAllItems}
					/>
				</Column>
			</Row>
			<div class="statements">
				{#if func.functionStatement.case == 'pythonFunction'}
					<Row>
						<Column>
							<TextInput
								labelText="Python Function"
								disabled={readonly}
								bind:value={func.functionStatement.value}
							/>
						</Column>
					</Row>
				{:else if func.functionStatement.case == 'sqlCode'}
					<Row>
						<Column
							><TextArea
								labelText="SQL Statement"
								disabled={readonly}
								bind:value={func.functionStatement.value}
							/></Column
						>
					</Row>
				{/if}
			</div>
		</Grid>

		<Button disabled={readonly} type="submit">Save</Button>
	</Form>
</div>

<style>
	.statements :global(input[type='text']),
	.statements :global(textarea) {
		font-family: monospace;
	}

	.local :global(.bx--label--disabled),
	.local :global(input:disabled),
	.local :global(textarea:disabled),
	.local :global(span.bx--list-box__label) {
		-webkit-text-fill-color: #777777;
		color: #777777;
	}
</style>
