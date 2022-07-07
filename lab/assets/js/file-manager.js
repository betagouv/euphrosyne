import { displayMessage } from "./utils.js";
import runDataService from "./run-data-service.js";

export class FileManager {
  constructor(projectName, runName, dataType, fileForm, fileTable) {
    this.projectName = projectName;
    this.runName = runName;
    this.dataType = dataType;

    this.fileForm = fileForm;
    this.fileTable = fileTable;

    this.fileTable.addEventListener("download-click", (e) => {
      const { name } = e.detail;
      this.downloadFile(name);
    });
    this.fileTable.addEventListener("delete-click", (e) => {
      const { name } = e.detail;
      this.deleteFile(name);
    });

    this.fileForm?.addEventListener("submit", (event) => {
      const { files } = event.target.elements.namedItem("files");
      this.uploadFiles(files);
    });
  }

  async fetchFiles() {
    this.fileTable.showLoading();
    const files = await runDataService.listData({
      projectName: this.projectName,
      runName: this.runName,
      dataType: this.dataType,
    });
    this.fileTable.setFiles(files);
    this.fileTable.displayFiles();
  }

  async downloadFile(name) {
    const url = await runDataService.fetchPresignedURL({
      projectName: this.projectName,
      runName: this.runName,
      dataType: this.dataType,
      fileName: name,
    });
    window.open(url, "_blank");
  }

  async deleteFile(name) {
    if (
      !window.confirm(
        window.interpolate(window.gettext("Delete the document %s ?"), [name])
      )
    ) {
      return;
    }
    this.fileTable.showLoading();
    try {
      await runDataService.deleteFile({
        projectName: this.projectName,
        runName: this.runName,
        dataType: this.dataType,
        fileName: name,
      });
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
      results = await runDataService.uploadFiles(
        {
          rojectName: this.projectName,
          runName: this.runName,
          dataType: this.dataType,
        },
        files
      );
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
