"use strict";
import { jwtFetch } from "./jwt.js";
import { formatBytes } from "./utils.js";

export class RunData {
  constructor(name, key, lastModified, size) {
    this.name = name;
    this.key = key;
    this.lastModified = lastModified;
    this.size = formatBytes(size);
  }
}

class FileUploadError extends Error {
  constructor(response, file) {
    super(`Failed to upload document. Response status: ${response.status}`);
    this.file = file;
  }
}

async function listData({ projectName, runName, dataType }) {
  const response = await jwtFetch(
    `${process.env.EUPHROSYNE_TOOLS_API_URL}/data/${projectName}/runs/${runName}/${dataType}`,
    {
      method: "GET",
    }
  );
  if (response.ok) {
    const files = await response.json();
    return files.map(
      (file) => new RunData(file.name, file.path, file.last_modified, file.size)
    );
  } else {
    throw new Error(
      `Failed to fetch document list. Response status: ${response.status}`
    );
  }
}

async function deleteFile({ projectName, runName, dataType, fileName }) {
  const url = await fetchPresignedURL({
    projectName,
    runName,
    dataType,
    fileName,
  });
  const response = await fetch(url, {
    method: "DELETE",
  });
  if (response.ok) {
    return response;
  } else {
    throw new Error(
      `Failed to delete document. Response status: ${response.status}`
    );
  }
}

async function uploadFiles({ projectName, runName, dataType }, files) {
  return await Promise.allSettled(
    Array.from(files).map(async (file) => {
      const url = await fetchPresignedURL({
        projectName,
        runName,
        dataType,
        fileName: file.name,
      });
      return uploadFile(file, url);
    })
  );
}

async function uploadFile(file, url) {
  const formData = new FormData();
  const response = await fetch(url, {
    method: "PUT",
    body: formData,
  });
  if (response.ok) {
    return { file, response };
  } else {
    throw new FileUploadError(response, file);
  }
}

async function fetchPresignedURL({ projectName, runName, dataType, fileName }) {
  const response = await jwtFetch(
    `${process.env.EUPHROSYNE_TOOLS_API_URL}/data/${projectName}/runs/${runName}/${dataType}/shared_access_signature/${fileName}`,
    {
      method: "GET",
    }
  );
  return (await response.json()).url;
}

const exports = {
  listData,
  deleteFile,
  fetchPresignedURL,
  uploadFiles,
};

export default exports;
