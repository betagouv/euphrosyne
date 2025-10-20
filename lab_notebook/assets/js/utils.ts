import { getExternalImageService } from "../../../lab/assets/js/external_image/registry";

export function extractPath(pathname: string) {
  // For EROS images
  if (pathname.startsWith("/eros")) {
    return pathname.split(".")[0].split("/").splice(-2).join("/");
  }
  // For Euphrosyne S3-stored images
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
    return getExternalImageService("eros").constructFromPath(
      path,
      euphrosyneToken,
    );
  } else if (path.startsWith("/joconde") || path.startsWith("/palissy")) {
    // POP images
    return getExternalImageService("pop").constructFromPath(path);
  }
  // For Euphorysne S3-stored images
  return `${baseUrl}${path}?${s3StorageToken}`;
}
