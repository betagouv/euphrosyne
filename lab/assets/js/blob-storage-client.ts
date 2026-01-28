"use strict";

import { BlockBlobClient } from "@azure/storage-blob";
import { StorageClient } from "./storage-service";

export class BlobStorageClient implements StorageClient {
  async upload(file: File, url: string) {
    await new BlockBlobClient(url).uploadData(await file.arrayBuffer());

    return { file };
  }
}
