"use strict";

import { FileTable } from "../../../../assets/js/components/file-table.js";
import { DocumentUploadForm } from "../components/document-upload-form.js";
import { FileManager } from "../../../../assets/js/file-manager.js";
import { DocumentPresignedUrlService } from "../presigned-url-service.js";
import { S3Service } from "../../../../assets/js/s3-service.js";

FileTable.init();
DocumentUploadForm.init();

const projectId = parseInt(document.URL.split("/").reverse()[1]);

const presignedUrlService = new DocumentPresignedUrlService(projectId);
const s3Service = new S3Service(presignedUrlService);

const documentTable = document.getElementById("document_list");
const documentForm = document.getElementById("upload-form");

const fileManager = new FileManager(
  documentForm,
  documentTable,
  presignedUrlService,
  s3Service
);

window.addEventListener("DOMContentLoaded", () => {
  fileManager.fetchFiles();
});
