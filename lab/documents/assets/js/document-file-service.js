"use strict";

import { FileService } from "../../../assets/js/file-service.js";
import { jwtFetch } from "../../../assets/js/jwt.js";

export class DocumentFileService extends FileService {
  constructor(projectName, projectSlug) {
    super(
      `/data/${projectSlug}/documents`,
      `/data/documents/shared_access_signature`
    );
    this.uploadPresignURL = `${process.env.EUPHROSYNE_TOOLS_API_URL}/data/${projectName}/documents/upload/shared_access_signature`;
  }

  async uploadFiles(files) {
    return await Promise.allSettled(
      Array.from(files).map(async (file) => {
        const url = await this.fetchUploadPresignedURL(file.name);
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
    const promises = [...Array(Math.ceil(batchNum)).keys()].map(
      (currentBatchNum) => {
        const batchStart = 4000000 * currentBatchNum,
          batchEnd =
            Math.ceil(batchNum) === currentBatchNum + 1
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

  async fetchUploadPresignedURL(fileName) {
    if (!this.uploadPresignURL) {
      throw new Error("uploadPresignURL must be specified");
    }
    const response = await jwtFetch(
      `${this.uploadPresignURL}?file_name=${encodeURIComponent(fileName)}`,
      {
        method: "GET",
      }
    );
    return (await response.json()).url;
  }
}
