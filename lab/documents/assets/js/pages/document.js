"use strict";

import { validateFileInput, uploadDocuments } from "../upload.js";
import { toggleLoading, fetchDocuments } from "../table.js";

import "@gouvfr/dsfr/dist/component/component.min.css";
import "@gouvfr/dsfr/dist/component/upload/upload.min.css";
import "../../css/project-documents.css";

const projectId = parseInt(document.URL.split("/").reverse()[1]);

window.addEventListener("DOMContentLoaded", () => {
  toggleLoading(true);
  fetchDocuments(projectId);
});

document
  .getElementById("upload-form")
  .addEventListener("uploadCompleted", () => {
    toggleLoading(true);
    fetchDocuments(projectId);
  });

document
  .querySelector("form#upload-form")
  .addEventListener("change", validateFileInput);
document
  .querySelector("form#upload-form")
  .addEventListener("submit", (event) => {
    event.preventDefault();
    event.target.querySelector("input[type='submit']").disabled = true;
    uploadDocuments(projectId);
  });
