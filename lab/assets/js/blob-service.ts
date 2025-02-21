// Upload blob to Azure

import { BlockBlobClient } from "@azure/storage-blob";

export async function uploadFile(file: File, url: string) {
  await new BlockBlobClient(url)
    .getBlockBlobClient()
    .uploadData(await file.arrayBuffer(), {
      blobHTTPHeaders: { blobCacheControl: "max-age=3400" },
    });

  return { file };
}
