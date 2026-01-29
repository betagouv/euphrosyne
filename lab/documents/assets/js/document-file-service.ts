"use strict";

import { FileService } from "../../../assets/js/file-service";
import { StorageClient } from "../../../assets/js/storage-service";
import { FileshareStorageClient } from "../../../assets/js/fileshare-storage-client";

interface DocumentFileServiceOptions {
  fetchFn?: typeof fetch;
  storageClient?: StorageClient;
}

export class DocumentFileService extends FileService {
  uploadPresignURL: string;
  private storageClient: StorageClient;

  constructor(
    projectName: string,
    projectSlug: string,
    fetchFn?: typeof fetch,
    storageClient?: StorageClient,
  );
  constructor(
    projectName: string,
    projectSlug: string,
    options?: DocumentFileServiceOptions,
  );
  constructor(
    projectName: string,
    projectSlug: string,
    fetchFnOrOptions?: typeof fetch | DocumentFileServiceOptions,
    storageClient?: StorageClient,
  ) {
    const options =
      typeof fetchFnOrOptions === "function"
        ? { fetchFn: fetchFnOrOptions, storageClient }
        : (fetchFnOrOptions ?? {});
    super(
      `/data/${projectSlug}/documents`,
      `/data/documents/shared_access_signature`,
      options.fetchFn,
    );
    this.uploadPresignURL = `/data/${projectName}/documents/upload/shared_access_signature`;
    this.storageClient = options.storageClient ?? new FileshareStorageClient();
  }

  uploadFiles(files: File[]) {
    return files.map(async (file) => {
      const url = await this.fetchUploadPresignedURL(file.name);
      return this.uploadFile(file, url);
    });
  }

  uploadFile(file: File, url: string) {
    return this.storageClient.upload(file, url);
  }

  async fetchUploadPresignedURL(fileName: string) {
    if (!this.uploadPresignURL) {
      throw new Error("uploadPresignURL must be specified");
    }
    const response = await this.fetchFn(
      `${this.uploadPresignURL}?file_name=${encodeURIComponent(fileName)}`,
      {
        method: "GET",
      },
    );
    if (!response?.ok) throw new Error("Failed to fetch upload presigned URL");
    return (await response.json()).url as string;
  }
}
