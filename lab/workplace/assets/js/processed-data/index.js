"use strict";

import { FileManager } from "../../../../assets/js/file-manager.js";
import { S3Service } from "../../../../assets/js/s3-service.js";

import { ProcessedDataPresignedUrlService } from "./presigned-url-service.js";

export function initProcessedData() {
  const projectId = parseInt(document.URL.split("/").reverse()[1]);

  window.runIds.forEach((runId) => {
    const presignedUrlService = new ProcessedDataPresignedUrlService(
        projectId,
        runId
      ),
      s3Service = new S3Service(presignedUrlService);

    const fileTable = document.querySelector(
        `#run-${runId}-processed-data-table`
      ),
      fileForm = document.querySelector(
        `#run-${runId}-processed-data-upload-form`
      );

    const fileManager = new FileManager(
      fileForm,
      fileTable,
      presignedUrlService,
      s3Service
    );

    window.addEventListener("DOMContentLoaded", () => {
      fileManager.fetchFiles();
    });
  });
}
