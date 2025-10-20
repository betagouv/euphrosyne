import { getExternalImageService } from "../../../lab/assets/js/external_image/registry";
import { ImageProvider } from "./IImageTransform";

export function extractPath(pathname: string, provider: ImageProvider): string {
  // For EROS images
  if (provider === "eros") {
    return pathname.split(".")[0].split("/").splice(-2).join("/");
  }
  // For Euphrosyne S3-stored images
  return pathname;
}

export function extractProviderFromPath(path: string): ImageProvider {
  if (
    (path.startsWith("C2RMF") ||
      path.startsWith("FZ") ||
      path.startsWith("F")) &&
    path.split("/").length === 2
  ) {
    return "eros";
  } else if (path.startsWith("/joconde") || path.startsWith("/palissy")) {
    return "pop";
  }
  return "euphrosyne";
}

export function constructImageStorageUrl(
  path: string,
  baseUrl: string,
  s3StorageToken: string,
  euphrosyneToken?: string,
) {
  // For EROS images
  const provider = extractProviderFromPath(path);
  if (provider === "eros") {
    return getExternalImageService("eros").constructFromPath(
      path,
      euphrosyneToken,
    );
  } else if (provider === "pop") {
    // POP images
    return getExternalImageService("pop").constructFromPath(path);
  }
  // For Euphrosyne S3-stored images
  return `${baseUrl}${path}?${s3StorageToken}`;
}
