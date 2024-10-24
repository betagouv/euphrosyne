"use strict";

import { uploadFile } from "../../../assets/js/fileshare-service";
import { FileService } from "../../../assets/js/file-service";
import { jwtFetch } from "../../../assets/js/jwt";

export class DocumentFileService extends FileService {
  uploadPresignURL: string;

  constructor(projectName: string, projectSlug: string) {
    super(
      `/data/${projectSlug}/documents`,
      `/data/documents/shared_access_signature`,
    );
    this.uploadPresignURL = `${process.env.EUPHROSYNE_TOOLS_API_URL}/data/${projectName}/documents/upload/shared_access_signature`;
  }

  uploadFiles(files: File[]) {
    return files.map(async (file) => {
      const url = await this.fetchUploadPresignedURL(file.name);
      return this.uploadFile(file, url);
    });
  }

  uploadFile(file: File, url: string) {
    return uploadFile(file, url);
  }

  async fetchUploadPresignedURL(fileName: string) {
    if (!this.uploadPresignURL) {
      throw new Error("uploadPresignURL must be specified");
    }
    const response = await jwtFetch(
      `${this.uploadPresignURL}?file_name=${encodeURIComponent(fileName)}`,
      {
        method: "GET",
      },
    );
    if (!response?.ok) throw new Error("Failed to fetch upload presigned URL");
    return (await response.json()).url;
  }
}
