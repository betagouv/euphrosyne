"use strict";

export interface StorageClient {
  upload(file: File, url: string): Promise<{ file: File }>;
}
