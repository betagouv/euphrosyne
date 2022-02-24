/**
 * Handles file upload to s3 bucket
 */
"use strict";

const FILES_MAX_SIZE = 30 * 1024 * 1000; // 30 MB
const MAX_SIZE_FORMATTED = "30 MB";
const ALLOWED_FILE_FORMATS = [
  "7z",
  "csv",
  "dat",
  "db",
  "dbf",
  "doc",
  "docx",
  "jpeg",
  "jpg",
  "heif",
  "log",
  "ods",
  "odt",
  "opd",
  "pdf",
  "png",
  "ppt",
  "pptx",
  "rar",
  "raw",
  "rtf",
  "sql",
  "svg",
  "tar.gz",
  "tiff",
  "txt",
  "wps",
  "wks",
  "wpd",
  "xls",
  "xlsx",
  "xml",
  "zip",
];

export class FileUploadForm extends HTMLFormElement {
  static init() {
    customElements.define("file-upload-form", FileUploadForm, {
      extends: "form",
    });
  }

  constructor() {
    super();
    this.addEventListener("change", this.validateFileInput);
    this.addEventListener("submit", (event) => {
      event.preventDefault();
    });
  }

  get files() {
    return this.querySelector("input[type='file']").files;
  }

  get projectId() {
    return this.getAttribute("project-id");
  }

  validateFileInput(event) {
    const fileInput = event.target;
    const { files } = fileInput;
    const totalSize = Array.from(files)
      .map((file) => file.size)
      .reduce((size, nextSize) => size + nextSize);

    fileInput.setCustomValidity("");

    if (totalSize > FILES_MAX_SIZE) {
      fileInput.setCustomValidity(
        window.interpolate(
          window.gettext("Total file sizes must not exceed %s."),
          [MAX_SIZE_FORMATTED]
        )
      );
      return;
    }
    const notSupportedFormats = Array.from(files)
      .map((file) => file.name.split(".").pop()?.toLowerCase())
      .filter((format) => ALLOWED_FILE_FORMATS.indexOf(format) === -1);
    if (notSupportedFormats.length > 0) {
      fileInput.setCustomValidity(
        window.interpolate(
          window.gettext("The following file formats are not accepted : %s"),
          [notSupportedFormats.join(", ")]
        )
      );
      return;
    }
  }

  toggleSubmitButton(disabled) {
    this.querySelector("input[type='submit']").disabled = disabled;
  }
}
