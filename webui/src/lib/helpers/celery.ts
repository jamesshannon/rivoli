import { createClient } from 'celery-node';

const client = createClient('redis://', 'redis://');

export function createTask(module: string, funcname: string, ...args: any[]) {
  const taskName = `${module}.${funcname}`;
  client.createTask(taskName).delay(...args);
}
