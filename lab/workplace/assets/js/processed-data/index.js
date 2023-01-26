"use strict";

import { FileManager } from "../../../../assets/js/file-manager.js";
import { ProcessedDataFileService } from "./processed-data-file-service.js";

export function initProcessedData() {
  window.runs.forEach((run) => {
    const fileTable = document.querySelector(
        `#run-${run.id}-processed-data-table`
      ),
      fileForm = document.querySelector(
        `#run-${run.id}-processed-data-upload-form`
      );

    const fileService = new ProcessedDataFileService(
      window.projectSlug,
      run.name
    );
    const fileManager = new FileManager(fileService, fileForm, fileTable);

    window.addEventListener("DOMContentLoaded", () => {
      fileManager.fetchFiles();
    });
  });
}
