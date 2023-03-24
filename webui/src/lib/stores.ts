import { writable } from 'svelte/store';

import type { Function } from './processor/protos/functions_pb';

let funcs: Array<Function> = [];
export const functionsStore = writable(funcs);
