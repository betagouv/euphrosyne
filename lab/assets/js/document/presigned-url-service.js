function handleResponse(event, resolve, reject) {
  const { readyState, status, response } = event.target;
  if (readyState == 4) {
    if (status === 200) {
      resolve(JSON.parse(response).url);
    } else {
      reject(event.target);
    }
  }
}

export function fetchDownloadPresignedURL(projectId, key, callbackFn) {
  return new Promise((resolve, reject) => {
    const request = new XMLHttpRequest();
    request.onreadystatechange = (event) =>
      handleResponse(event, resolve, reject);
    request.open(
      "GET",
      `/api/project/${projectId}/documents/presigned_download_url?key=${key}`,
      true
    );
    request.send();
  });
}

export function fetchDeletePresignedURL(projectId, key) {
  return new Promise((resolve, reject) => {
    const request = new XMLHttpRequest();
    request.onreadystatechange = (event) =>
      handleResponse(event, resolve, reject);
    request.open(
      "GET",
      `/api/project/${projectId}/documents/presigned_delete_url?key=${key}`,
      true
    );
    request.send();
  });
}

export function fetchListPresignedUrl(projectId) {
  return new Promise((resolve, reject) => {
    const request = new XMLHttpRequest();
    request.onreadystatechange = (event) =>
      handleResponse(event, resolve, reject);
    request.open(
      "GET",
      `/api/project/${projectId}/documents/presigned_list_url`,
      true
    );
    request.send();
  });
}

export function fetchUploadPresignedUrl(projectId) {
  return new Promise((resolve, reject) => {
    const request = new XMLHttpRequest();
    request.onreadystatechange = (event) =>
      handleResponse(event, resolve, reject);
    request.open(
      "GET",
      `/api/project/${projectId}/documents/presigned_post`,
      true
    );
    request.send();
  });
}
