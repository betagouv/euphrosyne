"use strict";

import {
  fetchDeletePresignedURL,
  fetchListPresignedUrl,
} from "./presigned-url-service.js";

export async function listObjectsV2(projectId) {
  const url = await fetchListPresignedUrl(projectId);
  const response = await fetch(url, {
    method: "GET",
  });
  if (response.ok) {
    const xml = new DOMParser().parseFromString(
      await response.text(),
      "application/xml"
    );
    return xml.querySelectorAll("Contents");
  } else {
    throw new Error(
      `Failed to fetch document list. Response status: ${response.status}`
    );
  }
}

export async function deleteObject(projectId, key) {
  const url = await fetchDeletePresignedURL(projectId, key);
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

export async function uploadObject(file, url, fields) {
  const formData = new FormData();
  const key = fields.key.replace("${filename}", file.name);
  formData.append("key", key);
  formData.append("Policy", fields.policy);
  formData.append("X-Amz-Signature", fields["x-amz-signature"]);
  formData.append("X-Amz-Date", fields["x-amz-date"]);
  formData.append("X-Amz-Credential", fields["x-amz-credential"]);
  formData.append("X-Amz-Algorithm", fields["x-amz-algorithm"]);
  formData.append("file", file);
  const response = await fetch(url, {
    method: "POST",
    body: formData,
  });
  if (response.ok) {
    return response;
  } else {
    throw new Error(
      `Failed to upload document. Response status: ${response.status}`
    );
  }
}
