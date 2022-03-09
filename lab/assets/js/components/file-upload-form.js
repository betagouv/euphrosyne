/**
 * Handles file upload to s3 bucket
 */
"use strict";

export class FileUploadForm extends HTMLFormElement {
  static init() {
    customElements.define("file-upload-form", FileUploadForm, {
      extends: "form",
    });
  }

  constructor() {
    super();
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

  toggleSubmitButton(disabled) {
    this.querySelector("input[type='submit']").disabled = disabled;
  }
}
