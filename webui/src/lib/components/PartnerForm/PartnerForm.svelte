<script lang="ts">
  import {createEventDispatcher} from "svelte";

  import {
    Form, FormLabel,
    Checkbox,
    Grid, Row, Column,
    TextInput,
    Button,
  } from "carbon-components-svelte";

	import { Partner } from "$lib/protos/config_pb";

  import StringMapping  from "$lib/components/StringMapping.svelte";

  export let partner: Partner | undefined = undefined;
  export let readonly: boolean = false;

  const dispatch = createEventDispatcher();

  if (! partner) {
    partner = new Partner();
  }

  function submitHandler() {
    dispatch('submit', {'partner': partner});
  }
</script>


<Form on:submit={submitHandler}>
  <Grid>
    <Row>
      <Column><TextInput labelText="Partner Name" {readonly} bind:value={partner.name} /></Column>
      <Column><Checkbox labelText="Active" {readonly} bind:checked={partner.active} /></Column>
    </Row>
    <Row>
      <Column>
        <FormLabel>Partner Tags</FormLabel>
        <StringMapping bind:staticTags={partner.staticTags} />
      </Column>
      <Column></Column>
    </Row>
  </Grid>

	<Button type="submit">Save</Button>
</Form>
