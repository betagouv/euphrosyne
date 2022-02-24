import { displayMessage } from "./utils.js";

export class FileManager {
  constructor(fileForm, fileTable, presignedUrlService, s3Service) {
    this.fileForm = fileForm;
    this.fileTable = fileTable;
    this.presignedUrlService = presignedUrlService;
    this.s3Service = s3Service;

    this.fileTable.addEventListener("download-click", (e) => {
      const { key } = e.detail;
      this.downloadFile(key);
    });
    this.fileTable.addEventListener("delete-click", (e) => {
      const { key } = e.detail;
      this.deleteFile(key);
    });

    this.fileForm?.addEventListener("submit", (event) => {
      const { files } = event.target.elements.namedItem("files");
      this.uploadFiles(files);
    });
  }

  async fetchFiles() {
    this.fileTable.showLoading();
    const s3Files = await this.s3Service.listObjectsV2();
    this.fileTable.setFiles(s3Files);
    this.fileTable.displayFiles();
  }

  async downloadFile(key) {
    const url = await this.presignedUrlService.fetchDownloadPresignedURL(key);
    window.open(url, "_blank");
  }

  async deleteFile(key) {
    if (
      !window.confirm(
        window.interpolate(window.gettext("Delete the document %s ?"), [
          key.split("/").pop(),
        ])
      )
    ) {
      return;
    }
    this.fileTable.showLoading();
    try {
      await this.s3Service.deleteObject(key);
      this.handleDeleteSuccess(key);
    } catch (error) {
      this.handleDeleteError(key);
      throw error;
    }
  }

  async uploadFiles(files) {
    let results;
    this.fileForm.toggleSubmitButton(true);
    try {
      results = await this.s3Service.uploadObjects(files);
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
    results.forEach((result) => {
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
          ]),
          "error"
        );
      }
    });
    if (results.map((result) => result.status === "fulfilled").indexOf !== -1) {
      this.fileTable.showLoading();
      this.fetchFiles();
    }
    this.fileForm.toggleSubmitButton(false);
    this.fileForm.reset();
  }

  handleDeleteError(key) {
    displayMessage(
      window.interpolate(window.gettext("File %s could not be removed."), [
        key.split("/").pop(),
      ]),
      "error"
    );
    this.fileTable.displayFiles();
  }

  handleDeleteSuccess(key) {
    this.fetchFiles();
    displayMessage(
      window.interpolate(window.gettext("File %s has been removed."), [
        key.split("/").pop(),
      ]),
      "success"
    );
  }
}
