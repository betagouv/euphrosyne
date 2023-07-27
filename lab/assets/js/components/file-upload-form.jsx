import React, { useRef } from "react";
import { displayMessage } from "../utils";

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

export default function FileUploadForm({
  fileService,
  onUploadSuccess,
  onUploadError,
  hintText = null,
}) {
  const fileInputRef = useRef(null),
    formRef = useRef(null);

  const onFormSubmit = (event) => {
    event.preventDefault();
    const { files } = event.target.elements.namedItem("files");
    uploadFiles(files);
  };

  const uploadFiles = async (files) => {
    let results;
    toggleSubmitButton(true);
    try {
      results = await fileService.uploadFiles(files);
    } catch (error) {
      displayMessage(
        window.gettext(
          "An error has occured while generating the presigned URL. Please contact the support team."
        ),
        "error"
      );
      toggleSubmitButton(false);
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
        onUploadError();
        await fileService.deleteFile(result.reason.file.name);
      }
    });
    if (results.map((result) => result.status === "fulfilled").indexOf !== -1) {
      onUploadSuccess();
    }
    toggleSubmitButton(false);
    formRef.current.reset();
  };

  const toggleSubmitButton = (disabled) => {
    fileInputRef.current.disabled = disabled;
  };

  const validateFileInput = (event) => {
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
  };

  return (
    <form ref={formRef} onSubmit={onFormSubmit}>
      <div className="fr-mb-4w">
        <div className="fr-upload-group">
          <label className="fr-label" htmlFor="file-upload">
            {window.gettext("Add files")}
            {hintText && <span className="fr-hint-text">{hintText}</span>}
          </label>
          <input
            ref={fileInputRef}
            className="fr-upload"
            type="file"
            name="files"
            multiple
            required
            onChange={validateFileInput}
          />
        </div>
        <input
          value={window.gettext("Upload")}
          className="button fr-mt-2w"
          type="submit"
          id="upload-button"
        />
      </div>
    </form>
  );
}
