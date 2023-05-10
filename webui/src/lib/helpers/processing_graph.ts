import type {
  FileType,
  RecordType,
  FieldType,
  FunctionConfig,
  Output
} from '$lib/rivoli/protos/config_pb';
import type { Function } from '$lib/rivoli/protos/functions_pb';

import ELK from 'elkjs/lib/elk.bundled.js';

export class Node {
  id = '';
  name = '';

  width = 280;
  height = 150;
  svelteComponentName: string = 'DefaultNode';
  isValidation = false;

  position: { x: number; y: number } | undefined;

  inputs: Array<Node> = [];
  outputs: Array<Node> = [];

  constructor(id: string, name: string) {
    this.id = id;
    this.name = name;
  }

  addInput(input: Node, reciprocate = true) {
    this.inputs.push(input);
    if (reciprocate) {
      input.addOutput(this, false);
    }
  }

  getInputIDs(): Array<string> {
    return this.inputs.map((n) => n.id);
  }

  addOutput(output: Node, reciprocate = true) {
    this.outputs.push(output);
    if (reciprocate) {
      output.addInput(this, false);
    }
  }

  toJSON() {
    return { id: this.id, inputs: this.getInputIDs() };
  }
}

class FileTypeCreateNode extends Node {
  svelteComponentName = 'CreateNode';

  constructor(ft: FileType) {
    super(`FILE-CREATE-${ft.id}`, ft.name);
  }
}

class FileTypeEndNode extends Node {
  constructor(ft: FileType) {
    super(`FILE-END-${ft.id}`, ft.name);
  }
}

class RecordTypeLoadNode extends Node {
  svelteComponentName = 'LoadNode';

  constructor(rt: RecordType) {
    super(`RECORD-LOAD-${rt.id}`, rt.name);
  }
}

class RecordTypeEndNode extends Node {
  isValidation = true;

  constructor(rt: RecordType) {
    super(`RECORD-END-${rt.id}`, rt.name);
  }
}

class FieldTypeParseNode extends Node {
  // Parsing is actually done on the record level, but we treat this as the
  // field "starting point".
  svelteComponentName = 'ParseNode';

  constructor(ft: FieldType) {
    super(`FIELD-PARSE-${ft.id}`, ft.name);
  }
}

export class ValidationNode extends Node {
  svelteComponentName = 'ValidateNode';
  isValidation = true;

  cfg: FunctionConfig;
  record: RecordType;
  field: FieldType | undefined;

  width = 450;
  height = 150;

  constructor(
    cfg: FunctionConfig,
    functions: Map<string, Function>,
    record: RecordType,
    field?: FieldType
  ) {
    super(`FUNC-${cfg.id}`, functions.get(cfg.functionId)!.name);
    this.cfg = cfg;
    this.record = record;
    this.field = field;
  }
}

export class RecordUploadNode extends Node {
  svelteComponentName = 'UploadNode';

  cfg: FunctionConfig;
  record: RecordType;

  width = 450;
  height = 150;

  constructor(
    cfg: FunctionConfig,
    functions: Map<string, Function>,
    record: RecordType
  ) {
    super(`FUNC-${cfg.id}`, functions.get(cfg.functionId)!.name);
    this.cfg = cfg;
    this.record = record;
  }
}

class OutputNode extends Node {
  svelteComponentName = 'OutputNode';

  constructor(out: Output) {
    super(`OUTPUT-${out.id}`, out.name);
  }
}

export function makeGraph(
  ft: FileType,
  functions: Map<string, Function>
): Map<string, Node> {
  const nodes = new Map<string, Node>();
  // const vertices = new Map<string, Node>();
  // const edges = [];

  // vertices.set('INPUT', new Node('INPUT', 'GENERIC'));

  let ftCreateNode = new FileTypeCreateNode(ft);
  // let ftEndNode = new FileTypeEndNode(ft);

  nodes.set(ftCreateNode.id, ftCreateNode);
  // nodes.set(ftEndNode.id, ftEndNode);

  for (let rt of ft.recordTypes) {
    let rtLoadNode = new RecordTypeLoadNode(rt);
    let rtEndNode = new RecordTypeEndNode(rt);

    ftCreateNode.addOutput(rtLoadNode);

    nodes.set(rtLoadNode.id, rtLoadNode);
    nodes.set(rtEndNode.id, rtEndNode);

    for (let fld of rt.fieldTypes) {
      let fieldParseNode = new FieldTypeParseNode(fld);
      nodes.set(fieldParseNode.id, fieldParseNode);

      rtLoadNode.addOutput(fieldParseNode);

      let priorNode: Node = fieldParseNode;
      for (let val of fld.validations) {
        let fieldValidateNode = new ValidationNode(val, functions, rt, fld);
        nodes.set(fieldValidateNode.id, fieldValidateNode);
        priorNode.addOutput(fieldValidateNode);
        priorNode = fieldValidateNode;
      }

      priorNode.addOutput(rtEndNode);
    }
    // should there be an "unknown record types" node?

    let priorNode: Node = rtEndNode;
    for (let val of rt.validations) {
      let recordVlidateNode = new ValidationNode(val, functions, rt);
      nodes.set(recordVlidateNode.id, recordVlidateNode);
      priorNode.addOutput(recordVlidateNode);
      priorNode = recordVlidateNode;
    }

    if (rt.upload) {
      let uploadNode = new RecordUploadNode(rt.upload, functions, rt);
      nodes.set(uploadNode.id, uploadNode);
      priorNode.addOutput(uploadNode);
      priorNode = uploadNode;
    }

    // priorNode.addOutput(ftEndNode);

    for (let output of ft.outputs) {
      let outputNode = new OutputNode(output);
      nodes.set(outputNode.id, outputNode);
      priorNode.addOutput(outputNode);
    }
  }

  return nodes;
}

export async function calculatePlacement(
  nodes: Map<string, Node>
): Promise<
  [
    Map<string, Node>,
    [{ x: number; y: number }, { width: number; height: number }]
  ]
> {
  const nodesArr = Array.from(nodes.values());

  const graph = {
    id: 'root',
    layoutOptions: {
      'elk.algorithm': 'elk.layered',
      'elk.layered.nodePlacement.bk.fixedAlignment': 'BALANCED',
      'elk.layered.considerModelOrder.strategy': 'NODES_AND_EDGES',
      'elk.direction': 'DOWN',
      'elk.layered.highDegreeNodes.threshold': 10,
      'elk.layered.layering.strategy': 'INTERACTIVE',
      'elk.layered.nodePlacement.strategy': 'LINEAR_SEGMENTS'
    },
    // Lie to ELK about the node sizes to allow for additional padding
    children: nodesArr.map((n) => ({
      id: n.id,
      width: n.width * 1.2,
      height: n.height * 1.2,
      isValidation: n.isValidation
    })),
    edges: nodesArr
      .map((n) =>
        n.inputs.map((i) => ({
          id: `${i.id}-${n.id}`,
          sources: [i.id],
          targets: [n.id]
        }))
      )
      .flat()
  };

  const elk = new ELK();
  const result = await elk.layout(graph);

  let minLeft = 10000;
  let minTop = 10000;
  let maxRight = 0;
  let maxBottom = 0;

  for (let child of result.children!) {
    let pos = { x: child.x!, y: child.y! };
    nodes.get(child.id).position = pos;

    if (child.isValidation) {
      minLeft = Math.min(minLeft, pos.x);
      minTop = Math.min(minTop, pos.y);
      maxRight = Math.max(maxRight, pos.x);
      maxBottom = Math.max(maxBottom, pos.y);
    }
  }

  // Validation-related nodes have to be positioned within group
  for (let node of nodes.values()) {
    if (node.isValidation) {
      node.position!.x -= minLeft - 10;
      node.position!.y -= minTop - 10;
    }
  }

  let group: [{ x: number; y: number }, { width: number; height: number }] = [
    { x: minLeft - 10, y: minTop - 10 },
    {
      width: maxRight - minLeft + 450 + 20,
      height: maxBottom - minTop + 150 + 20
    }
  ];
  console.log(group);

  return [nodes, group];
}
