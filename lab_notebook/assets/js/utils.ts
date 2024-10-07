export function constructImageStorageUrl(
  path: string,
  baseUrl: string,
  token: string,
) {
  return `${baseUrl}${path}?${token}`;
}
