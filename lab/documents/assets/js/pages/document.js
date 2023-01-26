"use strict";

import { FileTable } from "../../../../assets/js/components/file-table.js";
import { DocumentUploadForm } from "../components/document-upload-form.js";
import { FileManager } from "../../../../assets/js/file-manager.js";
import { DocumentFileService } from "../document-file-service.js";

FileTable.init();
DocumentUploadForm.init();

const fileService = new DocumentFileService(
  window.projectName,
  window.projectSlug
);

const documentTable = document.getElementById("document_list");
const documentForm = document.getElementById("upload-form");

const fileManager = new FileManager(fileService, documentForm, documentTable);

window.addEventListener("DOMContentLoaded", () => {
  fileManager.fetchFiles();
});
