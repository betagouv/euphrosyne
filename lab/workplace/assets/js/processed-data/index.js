"use strict";

import { FileManager } from "../../../../assets/js/file-manager.js";

export function initProcessedData() {
  window.runs.forEach((run) => {
    const fileTable = document.querySelector(
        `#run-${run.id}-processed-data-table`
      ),
      fileForm = document.querySelector(
        `#run-${run.id}-processed-data-upload-form`
      );

    const fileManager = new FileManager(
      window.projectName,
      run.name,
      "processed_data",
      fileForm,
      fileTable
    );

    window.addEventListener("DOMContentLoaded", () => {
      fileManager.fetchFiles();
    });
  });
}
