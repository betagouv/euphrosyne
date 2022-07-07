"use strict";

import { FileManager } from "../../../../assets/js/file-manager.js";

export function initRawData() {
  window.runs.forEach((run) => {
    const fileTable = document.querySelector(`#run-${run.id}-raw-data-table`),
      fileForm = document.querySelector(`#run-${run.id}-raw-data-upload-form`);

    const fileManager = new FileManager(
      window.projectName,
      run.name,
      "raw_data",
      fileForm,
      fileTable
    );

    window.addEventListener("DOMContentLoaded", () => {
      fileManager.fetchFiles();
    });
  });
}
