"use strict";

import { FileManager } from "../../../../assets/js/file-manager.js";
import { RawDataFileService } from "./raw-data-file-service.js";

export function initRawData() {
  window.runs.forEach((run) => {
    const fileTable = document.querySelector(`#run-${run.id}-raw-data-table`),
      fileForm = document.querySelector(`#run-${run.id}-raw-data-upload-form`);

    const fileService = new RawDataFileService(window.projectSlug, run.name);
    const fileManager = new FileManager(fileService, fileForm, fileTable);

    window.addEventListener("DOMContentLoaded", () => {
      fileManager.fetchFiles();
    });
  });
}
