import { http } from './http.ts';
import { mock } from './mock.ts';
import type { ApiClient } from './types.ts';

const USE_MOCK = false;

export const api: ApiClient = USE_MOCK ? mock : http;
