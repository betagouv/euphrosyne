"use strict";
import { jwtFetch } from "./jwt.js";

class EuphrosyneFile {
  constructor(name, key, lastModified, size) {
    this.name = name;
    this.key = key;
    this.lastModified = lastModified;
    this.size = size;
  }
}

class FileUploadError extends Error {
  constructor(response, file) {
    super(`Failed to upload file. Response status: ${response.status}`);
    this.file = file;
  }
}

// Service to manage files on an Azure Fileshare
export class FileService {
  constructor(listFileURL, fetchPresignedURL) {
    this.listFileURL = `${process.env.EUPHROSYNE_TOOLS_API_URL}${listFileURL}`;
    this.presignURL = `${process.env.EUPHROSYNE_TOOLS_API_URL}${fetchPresignedURL}`;
  }

  async listData() {
    const response = await jwtFetch(this.listFileURL, {
      method: "GET",
    });
    if (response.ok) {
      const files = await response.json();
      return files.map(
        (file) =>
          new EuphrosyneFile(
            file.name,
            file.path,
            new Date(file.last_modified),
            file.size
          )
      );
    } else if (response.status === 404) {
      return [];
    } else {
      throw new Error(
        `Failed to fetch file list. Response status: ${response.status}`
      );
    }
  }

  async deleteFile(fileName) {
    const url = await this.fetchPresignedURL(fileName);
    const response = await fetch(url, {
      method: "DELETE",
    });
    if (response.ok) {
      return response;
    } else {
      throw new Error(
        `Failed to delete file. Response status: ${response.status}`
      );
    }
  }

  async uploadFiles(files) {
    return await Promise.allSettled(
      Array.from(files).map(async (file) => {
        const url = await this.fetchPresignedURL(file.name);
        return this.uploadFile(file, url);
      })
    );
  }

  async uploadFile(file, url) {
    // File upload in an Azure Fileshare is divided in two steps :

    // 1. Creation of an empty file
    await this.createEmptyFile(url, file);

    // 2. Upload file content. If the file size is greater than 4 Mb, it must be
    // uploaded in several batches.
    const batchNum = file.size / 4000000;
    const promises = [...Array(Math.round(batchNum)).keys()].map(
      (currentBatchNum) => {
        const batchStart = 4000000 * currentBatchNum,
          batchEnd =
            Math.round(batchNum) === currentBatchNum + 1
              ? file.size
              : (currentBatchNum + 1) * 4000000;
        return this.uploadBytesToFile(
          url,
          file.slice(batchStart, batchEnd),
          batchStart,
          batchEnd - 1
        );
      }
    );

    const allSettledPromises = await Promise.allSettled(promises);

    // Throw error if any upload fail
    for (const promise of allSettledPromises) {
      if (promise.status === "rejected") {
        throw { file, value: promise.value };
      }
    }

    return { file };
  }

  async fetchPresignedURL(fileName) {
    const response = await jwtFetch(`${this.presignURL}/${fileName}`, {
      method: "GET",
    });
    return (await response.json()).url;
  }

  async createEmptyFile(presignedURL, file) {
    const response = await fetch(presignedURL, {
      method: "PUT",
      headers: {
        "Content-Length": 0,
        "x-ms-type": "file",
        "x-ms-content-length": file.size,
        "x-ms-version": "2021-08-06",
      },
    });
    if (!response.ok) {
      throw new FileUploadError(response, file);
    }
  }

  uploadBytesToFile(presignedURL, blob, fileByteStart, fileByteEnd) {
    return fetch(presignedURL + "&comp=range", {
      method: "PUT",
      body: blob,
      headers: {
        "x-ms-range": `bytes=${fileByteStart}-${fileByteEnd}`,
        "x-ms-write": "update",
        "x-ms-version": "2021-08-06",
      },
    });
  }
}
