<script lang="ts">
  import { createEventDispatcher, getContext } from 'svelte';

  import {
    ComboBox,
    Grid,
    Row,
    Column,
    Modal,
    TextInput
  } from 'carbon-components-svelte';

  import SvelteMarkdown from 'svelte-markdown';

  import { FunctionConfig } from '$lib/rivoli/protos/config_pb';
  import {
    type Function,
    Function_DataType,
    Function_FunctionType
  } from '$lib/rivoli/protos/functions_pb';

  import { makeObjectId } from '$lib/helpers/utils';
  import Fuse from 'fuse.js';

  export let functionType: Function_FunctionType | Array<Function_FunctionType>;
  export let functionConfig: FunctionConfig | undefined;
  export let open = false;

  let functionsMap: Map<string, Function> = getContext('FUNCTIONS');

  // Allow functionType to be passed as a single value or an array. Coerce it
  // into an array here
  if (!Array.isArray(functionType)) {
    functionType = [functionType];
  }

  // Copy any bound functionConfig value to a local variable so that we don't
  // modify the value in the form -- only bubble up the changes on save
  let localFunctionCfg: FunctionConfig;
  let func: Function | undefined;

  let selectedId: string | undefined;

  const dispatch = createEventDispatcher();

  // Define a lot of variables that won't be set until the modal is first
  // opened since the function items list is dependent on the selectedId.
  type Item = {id: string; text: string; summary: string; description: string;};
  let allItems: Item[];
  let items: Item[];
  let fuse: Fuse<Item>;

  const fuseOptions = {
    keys: [
      { name: 'text', weight: 0.7 },
      { name: 'description', weight: 0.3 }
    ],
    includeScore: true
  };

  function saveChanges() {
    // Dispatch the functionConfig upward, but only if it's been set up in the
    // modal, which is roughly equivalent to being picked in the dropdown.
    if (localFunctionCfg.functionId) {
      console.log('updating', localFunctionCfg);
      dispatch('save', { functionConfig: localFunctionCfg });
    } else {
      dispatch('save', { functionConfig: null });
    }

    open = false;
  }

  // either get a functionConfig or not.
  // if functionConfig then
  function openHandler() {
    if (functionConfig) {
      localFunctionCfg = functionConfig.clone();
      console.log(functionConfig, localFunctionCfg);
    } else {
      console.log('creating new functionconfig');
      localFunctionCfg = new FunctionConfig({
        id: makeObjectId()
      });
    }

    // This causes reactivity, and for updateEditor to be called a second time
    selectedId = localFunctionCfg.functionId || undefined;

    // Update allItems now that we have the selectedId. This ensures that any
    // deactivated functions are included in the list if they're selected.
    // Create an array of Combobox-friendly object-ized Functions of *just* the
    // Functions of the correct type
    allItems = Array.from(functionsMap.values())
      .filter((f) =>
        (functionType as Array<Function_FunctionType>).includes(f.type) &&
        (f.active || f.id == selectedId)
      )
      .map((f) => ({
        id: f.id,
        text: f.name,
        summary: f.description.split('\n', 1)[0],
        description: f.description
      }));

    fuse = new Fuse(allItems, fuseOptions);

    // updateEditor() updates the items copy
    updateEditor(true);
  }

  function updateEditor(force: boolean = false, _: string | null = null) {
    console.log('inside updateEditor')
    if (open) {
      const selectedFunctionUpdated = (localFunctionCfg.functionId || '') != (selectedId || '');
      console.log('inside updateeditor.open', force, localFunctionCfg.functionId, selectedId, selectedFunctionUpdated);
      if (force || selectedFunctionUpdated) {
        console.log('-- doing stuff inside if statement')
        localFunctionCfg.functionId = selectedId || '';

        // Set the func variable, to which the left-hand side of the form is
        // bound
        ////// What about preexisting parameters??????
        if (selectedId) {
          func = functionsMap.get(selectedId);
          if (selectedFunctionUpdated) {
            localFunctionCfg.parameters = func!.parameters.map(() => '');
          }
        } else {
          func = undefined;
          localFunctionCfg.parameters = [];
        }

        // Duplicate allItems to items, which is used by the Combobox
        items = [... allItems];
      }

      console.log('config id', localFunctionCfg?.id, localFunctionCfg.functionId, selectedId);
    }
  }

  // Combobox - On Change, including first load
  // NB: The on:select handler doesn't get called on *un*select
  $: updateEditor(false, selectedId);

  function filterItems(pattern: KeyboardEvent) {
    console.log('searching for ', pattern.target!.value)
    const qs = (pattern.target! as HTMLInputElement).value;
    if (! qs) {
      // Should also check if qs is a full function name and it's the selected
      // id. In that case it's a dropdown after the selection and the
      // list should be reset.
      items = [... allItems];
    } else {
      items = fuse.search(qs, { limit: 10 }).map((r) => r.item);
    }
  }
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
          <ComboBox {items} on:keyup={filterItems} bind:selectedId let:item>
            <div>
              <strong><code>{item.text}</code></strong>
            </div>
            <div>
              {item.summary}
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
          <Column class="function_description">
            <SvelteMarkdown source={func.description} />
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
            {#if func.parameters.length && localFunctionCfg}
              {#each localFunctionCfg.parameters as value}
                <TextInput bind:value />
              {/each}
            {:else}
              <p>
                There is no configuration required as this function doens't take
                any parameters.
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

  .local :global(.function_description ul) {
    list-style-type: circle;
    list-style-position: inside;
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
