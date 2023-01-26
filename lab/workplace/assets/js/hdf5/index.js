"use strict";

import { FileManager } from "../../../../assets/js/file-manager.js";
import { HDF5FileService } from "./hdf5-file-service.js";

export function initHDF5() {
  window.runs.forEach((run) => {
    const fileTable = document.querySelector(`#run-${run.id}-hdf5-table`);

    const fileService = new HDF5FileService(window.projectSlug, run.name);
    const fileManager = new FileManager(fileService, null, fileTable);

    window.addEventListener("DOMContentLoaded", () => {
      fileManager.fetchFiles();
    });
  });
}
