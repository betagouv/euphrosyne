import {
  fetchDeletePresignedURL,
  fetchListPresignedUrl,
} from "./presigned-url-service";

export function listObjectsV2(projectId) {
  return new Promise(async (resolve, reject) => {
    const url = await fetchListPresignedUrl(projectId);
    const request = new XMLHttpRequest();
    request.onreadystatechange = (event) => {
      const { readyState, status, response } = event.target;
      if (readyState == 4) {
        if (status == 200) {
          const xml = new DOMParser().parseFromString(
            response,
            "application/xml"
          );
          resolve(xml.querySelectorAll("Contents"));
        } else {
          reject(response);
        }
      }
    };
    request.open("GET", url, true);
    request.send();
  });
}

export function deleteObject(projectId, key) {
  return new Promise(async (resolve, reject) => {
    let url;
    try {
      url = await fetchDeletePresignedURL(projectId, key);
    } catch (error) {
      reject(error);
    }
    const request = new XMLHttpRequest();
    request.onreadystatechange = (event) => {
      const { readyState, status } = event.target;
      if (readyState == 4) {
        if (status == 204) {
          resolve();
        } else {
          reject();
        }
      }
    };
    request.open("DELETE", url, true);
    request.send();
  });
}

export function uploadObject(file, url, fields) {
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
