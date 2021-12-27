/**
 * Handles file upload to s3 bucket
 */
(function (projectId) {
  const FILES_MAX_SIZE = 30 * 1024 * 1000; // 30 MB
  const MAX_SIZE_FORMATTED = "30 MB";

  // FUNCTION DECLARATIONS

  function validateFileInput(event) {
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

  function getPresignedUrl(projectId) {
    const request = new XMLHttpRequest();
    request.onreadystatechange = handlePresignedURLResponse;
    request.open(
      "GET",
      `/api/project/${projectId}/documents/presigned_post`,
      true
    );
    request.send();
  }

  async function handlePresignedURLResponse(event) {
    /**
     * On server response, uses the presigned URL to upload files
     * to s3 bucket. Displays messages to user on success / error.
     */
    if (event.target.readyState == 4) {
      const form = document.getElementById("upload-form");
      if (event.target.status == 200) {
        const { url, fields } = JSON.parse(event.target.response).url;
        const files = document.querySelector("input[type='file']").files;

        const responses = await Promise.all(
          Array.from(files).map((file) => uploadDocument(file, url, fields))
        );
        responses.forEach((response) => {
          displayResponseMessage(response);
          const { status } = response;
          if (status >= 200 && status < 300) {
            form.dispatchEvent(new Event("uploadCompleted"));
          }
        });
        form.reset();
      } else {
        displayMessage(
          gettext(
            "An error has occured while generating the presigned URL. Please contact the support team."
          ),
          "error"
        );
      }
      form.querySelector("input[type='submit']").disabled = false;
    }
  }

  function uploadDocument(file, url, fields) {
    /**
     * Does the actual upload. Return a promise so we can wait
     * for all file uploads to end.
     */
    return new Promise((resolve, reject) => {
      const formData = new FormData();
      const key = fields.key.replace("${filename}", file.name);
      formData.append("key", key);
      formData.append("Policy", fields.policy);
      formData.append("X-Amz-Signature", fields["x-amz-signature"]);
      formData.append("X-Amz-Date", fields["x-amz-date"]);
      formData.append("X-Amz-Credential", fields["x-amz-credential"]);
      formData.append("X-Amz-Algorithm", fields["x-amz-algorithm"]);
      formData.append("file", file);

      const request = new XMLHttpRequest();
      request.addEventListener("load", (event) => {
        resolve(event.target);
      });
      request.addEventListener("error", (event) => {
        reject(event.target);
      });
      request.open("POST", `${url}/${key}`, true);
      request.send(formData);
    });
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

  // EVENT HANDLERS

  document
    .querySelector("form#upload-form")
    .addEventListener("change", validateFileInput);
  document
    .querySelector("form#upload-form")
    .addEventListener("submit", (event) => {
      event.preventDefault();
      event.target.querySelector("input[type='submit']").disabled = true;
      getPresignedUrl(projectId);
    });
})(projectId);
