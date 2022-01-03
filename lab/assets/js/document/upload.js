/**
 * Handles file upload to s3 bucket
 */
"use strict";
import { fetchUploadPresignedUrl } from "./presigned-url-service.js";
import { uploadObject } from "./s3-service.js";
import { displayMessage } from "../utils.js";

const FILES_MAX_SIZE = 30 * 1024 * 1000; // 30 MB
const MAX_SIZE_FORMATTED = "30 MB";

export async function uploadDocuments(projectId) {
  try {
    const response = await fetchUploadPresignedUrl(projectId);
    handlePresignedURLResponse(response);
  } catch (error) {
    displayMessage(
      gettext(
        "An error has occured while generating the presigned URL. Please contact the support team."
      ),
      "error"
    );
    form.querySelector("input[type='submit']").disabled = false;
  }
}

export function validateFileInput(event) {
  const fileInput = event.target;
  const { files } = fileInput;
  const totalSize = Array.from(files)
    .map((file) => file.size)
    .reduce((size, nextSize) => size + nextSize);

  if (totalSize > FILES_MAX_SIZE) {
    fileInput.setCustomValidity(
      interpolate(gettext("Total file sizes must not exceed %s."), [
        MAX_SIZE_FORMATTED,
      ])
    );
  }
}

async function handlePresignedURLResponse(response) {
  /**
   * On server response, uses the presigned URL to upload files
   * to s3 bucket. Displays messages to user on success / error.
   */
  const form = document.getElementById("upload-form");
  const { url, fields } = response;
  const files = document.querySelector("input[type='file']").files;

  const responses = await Promise.all(
    Array.from(files).map((file) => uploadObject(file, url, fields))
  );
  responses.forEach((response) => {
    displayResponseMessage(response);
    const { status } = response;
    if (status >= 200 && status < 300) {
      form.dispatchEvent(new Event("uploadCompleted"));
    }
  });
  form.reset();
}

function displayResponseMessage(response) {
  /**
   * Displays a success / error message on s3 response.
   */
  const { status, responseURL } = response;
  if (status >= 200 && status < 300) {
    displayMessage(
      interpolate(gettext("File %s has been uploaded."), [
        responseURL.split("/").pop(),
      ]),
      "success"
    );
  } else {
    displayMessage(
      interpolate(gettext("File %s could not be uploaded."), [
        responseURL.split("/").pop(),
      ]),
      "error"
    );
  }
}
