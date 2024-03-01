import { displayMessage } from "./utils.js";

export class FileManager {
  constructor(fileService, fileForm, fileTable) {
    this.fileService = fileService;
    this.fileForm = fileForm;
    this.fileTable = fileTable;

    this.fileTable.addEventListener("download-click", (e) => {
      const { path } = e.detail;
      this.downloadFile(path);
    });
    this.fileTable.addEventListener("delete-click", (e) => {
      const { name, path } = e.detail;
      this.deleteFile(name, path);
    });

    this.fileForm?.addEventListener("submit", (event) => {
      const { files } = event.target.elements.namedItem("files");
      this.uploadFiles(Array.from(files));
    });
  }

  async fetchFiles() {
    this.fileTable.showLoading();
    const files = await this.fileService.listData();
    this.fileTable.setFiles(files);
    this.fileTable.displayFiles(false);
  }

  async downloadFile(path) {
    const url = await this.fileService.fetchPresignedURL(path);
    window.open(url, "_blank");
  }

  async deleteFile(name, path) {
    if (
      !window.confirm(
        window.interpolate(window.gettext("Delete the document %s ?"), [name])
      )
    ) {
      return;
    }
    this.fileTable.showLoading();
    try {
      await this.fileService.deleteFile(path);
      this.handleDeleteSuccess(name);
    } catch (error) {
      this.handleDeleteError(name);
      throw error;
    }
  }

  async uploadFiles(files) {
    let results;
    this.fileForm.toggleSubmitButton(true);
    try {
      results = await this.fileService.uploadFiles(files);
    } catch (error) {
      displayMessage(
        window.gettext(
          "An error has occured while generating the presigned URL. Please contact the support team."
        ),
        "error"
      );
      this.fileForm.toggleSubmitButton(false);
      throw error;
    }
    results.forEach(async (result) => {
      if (result.status === "fulfilled") {
        displayMessage(
          window.interpolate(window.gettext("File %s has been uploaded."), [
            result.value.file.name,
          ]),
          "success"
        );
      } else {
        displayMessage(
          window.interpolate(window.gettext("File %s could not be uploaded."), [
            result.reason.file.name,
          ]) +
            " " +
            result.reason.message,
          "error"
        );
        await this.fileService.deleteFile(result.reason.file.name);
      }
    });
    if (results.map((result) => result.status === "fulfilled").indexOf !== -1) {
      this.fileTable.showLoading();
      this.fetchFiles();
    }
    this.fileForm.toggleSubmitButton(false);
    this.fileForm.reset();
  }

  handleDeleteError(name) {
    displayMessage(
      window.interpolate(window.gettext("File %s could not be removed."), [
        name,
      ]),
      "error"
    );
    this.fileTable.displayFiles();
  }

  handleDeleteSuccess(name) {
    this.fetchFiles();
    displayMessage(
      window.interpolate(window.gettext("File %s has been removed."), [name]),
      "success"
    );
  }
}
