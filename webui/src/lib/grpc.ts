import { createPromiseClient } from '@bufbuild/connect';
import { createConnectTransport } from '@bufbuild/connect-web';
import { WebService } from '$lib/protos/web_service_connect';

const transport = createConnectTransport({ baseUrl: 'http://localhost:5051' });
export const client = createPromiseClient(WebService, transport);
