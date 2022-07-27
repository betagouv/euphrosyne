"use strict";
import { jwtFetch } from "./jwt.js";

export class EuphrosyneFile {
  constructor(name, path, lastModified, size) {
    this.name = name;
    this.path = path;
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

  async fetchPresignedURL(path) {
    const response = await jwtFetch(
      `${this.presignURL}?path=${encodeURIComponent(path)}`,
      {
        method: "GET",
      }
    );
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
