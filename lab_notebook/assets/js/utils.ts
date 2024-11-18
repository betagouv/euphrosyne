import { constructFromErosPath } from "../../../lab/assets/js/eros-service";

export function extractPath(pathname: string) {
  // For EROS images
  if (pathname.startsWith("/eros")) {
    return pathname.split(".")[0].split("/").splice(-2).join("/");
  }
  // For Euphorysne S3-stored images
  return pathname;
}

export function constructImageStorageUrl(
  path: string,
  baseUrl: string,
  s3StorageToken: string,
  euphrosyneToken?: string,
) {
  // For EROS images
  if (
    (path.startsWith("C2RMF") ||
      path.startsWith("FZ") ||
      path.startsWith("F")) &&
    path.split("/").length === 2
  ) {
    return constructFromErosPath(path, euphrosyneToken);
  }
  // For Euphorysne S3-stored images
  return `${baseUrl}${path}?${s3StorageToken}`;
}
