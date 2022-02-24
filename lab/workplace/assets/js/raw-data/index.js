"use strict";

import { FileManager } from "../../../../assets/js/file-manager.js";
import { S3Service } from "../../../../assets/js/s3-service.js";

import { RawDataPresignedUrlService } from "./presigned-url-service.js";

export function initRawData() {
  const projectId = parseInt(document.URL.split("/").reverse()[1]);

  window.runIds.forEach((runId) => {
    const presignedUrlService = new RawDataPresignedUrlService(
        projectId,
        runId
      ),
      s3Service = new S3Service(presignedUrlService);

    const fileTable = document.querySelector(`#run-${runId}-raw-data-table`),
      fileForm = document.querySelector(`#run-${runId}-raw-data-upload-form`);

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
