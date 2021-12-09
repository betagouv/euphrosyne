"use strict";

export function getCSRFToken() {
  // Get CSRF token from cookies
  // https://docs.djangoproject.com/en/4.0/ref/csrf/#ajax
  const cookieName = "csrftoken";
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, cookieName.length + 1) === cookieName + "=") {
        return decodeURIComponent(cookie.substring(cookieName.length + 1));
      }
    }
  }
  return null;
}

export function fetchURL(url) {
  return fetch(url, {
    method: "POST",
    headers: new Headers({
      "X-CSRFToken": getCSRFToken(),
    }),
  });
}

export async function fetchDownloadPresignedURL(projectId, key) {
  const response = await fetchURL(
    `/api/project/${projectId}/documents/presigned_download_url?key=${key}`
  );
  return (await response.json()).url;
}

export async function fetchDeletePresignedURL(projectId, key) {
  const response = await fetchURL(
    `/api/project/${projectId}/documents/presigned_delete_url?key=${key}`
  );
  return (await response.json()).url;
}

export async function fetchListPresignedUrl(projectId) {
  const response = await fetchURL(
    `/api/project/${projectId}/documents/presigned_list_url`
  );
  return (await response.json()).url;
}

export async function fetchUploadPresignedUrl(projectId) {
  const response = await fetchURL(
    `/api/project/${projectId}/documents/presigned_post`
  );
  return (await response.json()).url;
}
