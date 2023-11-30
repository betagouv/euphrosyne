/**
 * Handles file upload to s3 bucket
 */
"use strict";

import { FileUploadForm } from "../../../../assets/js/components/file-upload-form.js";

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
  "par",
  "nra",
  "xnra",
  "geo",
  "str",
  "spc",
  "prf",
  "tcn",
];

export class DocumentUploadForm extends FileUploadForm {
  static init() {
    customElements.define("document-upload-form", DocumentUploadForm, {
      extends: "form",
    });
  }

  constructor() {
    super();
    this.addEventListener("change", this.validateFileInput);
  }

  validateFileInput(event) {
    const fileInput = event.target;
    const { files } = fileInput;

    fileInput.setCustomValidity("");

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
}
