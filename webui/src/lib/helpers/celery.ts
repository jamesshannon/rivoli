import { env } from '$env/dynamic/private';

import { createClient } from 'celery-node';

const client = createClient(env.CELERY_REDIS_URL, env.CELERY_REDIS_URL);

export function createTask(module: string, funcname: string, args: any[], kwargs?: object) {
  const taskName = `${module}.${funcname}`;
  client.createTask(taskName).applyAsync(args, kwargs);
}
