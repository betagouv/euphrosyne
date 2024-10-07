// Upload blob to Azure

import { BlockBlobClient } from "@azure/storage-blob";

class FileUploadError extends Error {
  file: File;

  constructor(message: string, file: File) {
    super(message);
    this.file = file;
  }
}

export async function uploadFile(file: File, url: string) {
  await new BlockBlobClient(url)
    .getBlockBlobClient()
    .uploadData(await file.arrayBuffer());

  return { file };
}
