"use strict";

import { jwtFetch } from "./jwt.js";

type FileType = "file" | "directory";

export interface EuphrosyneFile {
  name: string;
  path: string;
  lastModified: Date;
  size: number | null;
  isDir: boolean;
}

interface ListDataResponseItem {
  name: string;
  path: string;
  last_modified: string;
  size: number;
  type?: FileType;
}

// Service to manage files on an Azure Fileshare
export class FileService {
  listFileURL: string;
  presignURL: string;

  constructor(listFileURL: string, fetchPresignedURL: string) {
    this.listFileURL = `${process.env.EUPHROSYNE_TOOLS_API_URL}${listFileURL}`;
    this.presignURL = `${process.env.EUPHROSYNE_TOOLS_API_URL}${fetchPresignedURL}`;
  }

  async listData(folder?: string): Promise<EuphrosyneFile[]> {
    let url = this.listFileURL;
    if (folder && folder !== "") {
      url += `?folder=${encodeURIComponent(folder)}`;
    }
    const fetchRequestInit: RequestInit = {
      method: "GET",
    };
    const response = await jwtFetch(url, fetchRequestInit);
    if (response?.ok) {
      const files = (await response.json()) as ListDataResponseItem[];
      return files.map(({ name, path, last_modified, size, type }) => ({
        name,
        path,
        size,
        lastModified: new Date(last_modified),
        isDir: type === "directory",
      }));
    } else if (response?.status === 404) {
      return [];
    } else {
      throw new Error(
        `Failed to fetch file list. Response status: ${response?.status}`,
      );
    }
  }

  async deleteFile(fileName: string) {
    const url = await this.fetchPresignedURL(fileName);
    const response = await fetch(url, {
      method: "DELETE",
    });
    if (response?.ok) {
      return response;
    } else {
      throw new Error(
        `Failed to delete file. Response status: ${response.status}`,
      );
    }
  }

  async fetchPresignedURL(path: string) {
    const response = await jwtFetch(
      `${this.presignURL}?path=${encodeURIComponent(path)}`,
      {
        method: "GET",
      },
    );
    if (!response?.ok) throw new Error("Failed to fetch presigned URL");
    return (await response.json()).url;
  }
}
