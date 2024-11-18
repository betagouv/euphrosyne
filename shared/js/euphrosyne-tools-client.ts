import { getToken, getAccessToken, jwtFetch } from "./jwt";

type ClientReponse = ReturnType<typeof fetch>;

let refreshPromise: Promise<string> | null = null;

async function _fetch(
  input: string | URL | globalThis.Request,
  init?: RequestInit,
  isRetry?: boolean,
): ClientReponse {
  const response = await fetch(input, init);
  if (response.status === 401 && !isRetry) {
    if (!refreshPromise) {
      refreshPromise = getToken(false) as Promise<string>;
    }
    const token = await refreshPromise;
    refreshPromise = null;

    return fetch(input, {
      ...init,
      headers: { ...init?.headers, Authorization: `Bearer ${token}` },
    });
  }
  return response;
}

export default async function euphrosyneToolsFetch(
  input: string | URL | globalThis.Request,
  init?: RequestInit,
): ClientReponse {
  const baseURL = process.env.EUPHROSYNE_TOOLS_API_URL;
  if (!baseURL) {
    console.warn("EUPHROSYNE_TOOLS_API_URL is not set");
  }
  return _fetch(`${baseURL}${input}`, {
    ...init,
    headers: {
      ...init?.headers,
      Authorization: `Bearer ${getAccessToken()}`,
    },
  });
}

export class EuphroToolsService {
  fetchFn: typeof euphrosyneToolsFetch;

  constructor(fetchFn?: typeof euphrosyneToolsFetch) {
    this.fetchFn = fetchFn || (jwtFetch as typeof euphrosyneToolsFetch);
  }
}
