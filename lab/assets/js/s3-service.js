"use strict";
import { formatBytes } from "./utils.js";
export class S3Service {
  constructor(presignedUrlService) {
    this.presignedUrlService = presignedUrlService;
  }

  async listObjectsV2() {
    const url = await this.presignedUrlService.fetchListPresignedUrl();
    const response = await fetch(url, {
      method: "GET",
    });
    if (response.ok) {
      const xml = new DOMParser().parseFromString(
        await response.text(),
        "application/xml"
      );
      return serializeS3ListObjectsV2Contents(xml.querySelectorAll("Contents"));
    } else {
      throw new Error(
        `Failed to fetch document list. Response status: ${response.status}`
      );
    }
  }

  async deleteObject(key) {
    const url = await this.presignedUrlService.fetchDeletePresignedURL(key);
    const response = await fetch(url, {
      method: "DELETE",
    });
    if (response.ok) {
      return response;
    } else {
      throw new Error(
        `Failed to delete document. Response status: ${response.status}`
      );
    }
  }

  async uploadObjects(files) {
    const { url, fields } =
      await this.presignedUrlService.fetchUploadPresignedUrl();
    return await Promise.allSettled(
      Array.from(files).map((file) => {
        return this.uploadObject(file, url, fields);
      })
    );
  }

  async uploadObject(file, url, fields) {
    const formData = new FormData();
    const key = fields.key.replace("${filename}", file.name);
    formData.append("key", key);
    formData.append("Policy", fields.policy);
    formData.append("X-Amz-Signature", fields["x-amz-signature"]);
    formData.append("X-Amz-Date", fields["x-amz-date"]);
    formData.append("X-Amz-Credential", fields["x-amz-credential"]);
    formData.append("X-Amz-Algorithm", fields["x-amz-algorithm"]);
    formData.append("file", file);
    const response = await fetch(url, {
      method: "POST",
      body: formData,
    });
    if (response.ok) {
      return { file, response };
    } else {
      throw new S3FileUploadError(response, file);
    }
  }
}

class S3FileUploadError extends Error {
  constructor(response, file) {
    super(`Failed to upload document. Response status: ${response.status}`);
    this.file = file;
  }
}

export class S3File {
  constructor(key, lastModified, size) {
    this.name = key.split("/").pop();
    this.key = key;
    this.lastModified = lastModified;
    this.size = size;
  }
}

export function serializeS3ListObjectsV2Contents(xmlContents) {
  return Array.from(xmlContents).map(
    (documentEl) =>
      new S3File(
        decodeURIComponent(documentEl.querySelector("Key").textContent),
        new Date(
          documentEl.querySelector("LastModified").textContent
        ).toLocaleDateString(),
        formatBytes(
          parseInt(documentEl.querySelector("Size").textContent || "0")
        )
      )
  );
}
