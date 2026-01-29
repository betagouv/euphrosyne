"use strict";

import { StorageClient } from "./storage-service";

// Upload blob to Azure
class FileUploadError extends Error {
  file: File;

  constructor(message: string, file: File) {
    super(message);
    this.file = file;
  }
}

export class FileshareStorageClient implements StorageClient {
  async upload(file: File, url: string) {
    // File upload in an Azure Fileshare is divided in two steps :

    // 1. Creation of an empty file
    await createEmptyFile(url, file);

    // 2. Upload file content. If the file size is greater than 4 Mb, it must be
    // uploaded in several batches.
    const batchNum = file.size / 4000000;
    const promises = [...Array(Math.ceil(batchNum)).keys()].map(
      (currentBatchNum) => {
        const batchStart = 4000000 * currentBatchNum,
          batchEnd =
            Math.ceil(batchNum) === currentBatchNum + 1
              ? file.size
              : (currentBatchNum + 1) * 4000000;
        return uploadBytesToFile(
          url,
          file,
          file.slice(batchStart, batchEnd),
          batchStart,
          batchEnd - 1,
        );
      },
    );
    const allSettledPromises = await Promise.allSettled(promises);

    // Throw error if any upload fail
    for (const promise of allSettledPromises) {
      if (promise.status === "rejected") {
        throw { file, value: promise.reason };
      }
    }

    return { file };
  }
}

async function createEmptyFile(presignedURL: string, file: File) {
  const response = await fetch(presignedURL, {
    method: "PUT",
    headers: {
      "Content-Length": "0",
      "x-ms-type": "file",
      "x-ms-content-length": file.size.toString(),
      "x-ms-version": "2021-08-06",
    },
  });
  if (!response.ok) {
    throw new FileUploadError(response.statusText, file);
  }
}

async function uploadBytesToFile(
  presignedURL: string,
  file: File,
  blob: BodyInit,
  fileByteStart: number,
  fileByteEnd: number,
) {
  const response = await fetch(presignedURL + "&comp=range", {
    method: "PUT",
    body: blob,
    headers: {
      "x-ms-range": `bytes=${fileByteStart}-${fileByteEnd}`,
      "x-ms-write": "update",
      "x-ms-version": "2021-08-06",
    },
  });
  if (!response.ok) {
    throw new FileUploadError(response.statusText, file);
  }
  return response;
}
