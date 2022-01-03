"use strict";

import { formatBytes, displayMessage } from "../utils";

export function toggleLoading(active) {
  if (active) {
    document
      .querySelectorAll("table#document_list tbody tr:not(.loading)")
      .forEach((el) => (el.style.display = "none"));
    document.querySelector(
      "table#document_list tbody tr.loading"
    ).style.display = "";
  } else {
    document
      .querySelectorAll("table#document_list tbody tr:not(.loading)")
      .forEach((el) => (el.style.display = ""));
    document.querySelector(
      "table#document_list tbody tr.loading"
    ).style.display = "none";
  }
}

export function fetchDocuments(projectId) {
  const request = new XMLHttpRequest();
  request.onreadystatechange = handlePresignedURLResponse;
  request.open(
    "GET",
    `/api/project/${projectId}/documents/presigned_list_url`,
    true
  );
  request.send();
}

function displayProjectDocuments(documentXMLEls) {
  toggleLoading(false);
  const tableBodyEl = document.querySelector("table#document_list tbody");
  tableBodyEl.querySelectorAll(".document-row").forEach((el) => el.remove());
  if (documentXMLEls.length) {
    document.querySelector("tr.no_data").style.display = "none";
    documentXMLEls.forEach((documentEl) => {
      const rowEl = document.createElement("tr");
      rowEl.classList.add("document-row");
      const keyEl = document.createElement("td");
      keyEl.innerText = documentEl
        .querySelector("Key")
        .textContent.split("/")
        .pop();
      const lastModifiedEl = document.createElement("td");
      lastModifiedEl.innerText = new Date(
        documentEl.querySelector("LastModified").textContent
      ).toLocaleDateString();
      const sizeEl = document.createElement("td");
      sizeEl.innerText = formatBytes(
        parseInt(documentEl.querySelector("Size").textContent || "0")
      );
      const actionsEl = document.createElement("td");
      actionsEl.appendChild(
        createActionCell(documentEl.querySelector("Key").textContent)
      );
      rowEl.appendChild(keyEl);
      rowEl.appendChild(lastModifiedEl);
      rowEl.appendChild(sizeEl);
      rowEl.appendChild(actionsEl);
      tableBodyEl.appendChild(rowEl);
    });
  } else {
    document.querySelector("tr.no_data").style.display = "";
  }
}
function handleListObjectV2Response(event) {
  if (event.target.readyState == 4 && event.target.status == 200) {
    const { response } = event.target;
    const xml = new DOMParser().parseFromString(response, "application/xml");
    const keys = xml.querySelectorAll("Contents");
    displayProjectDocuments(keys);
  }
}
function handlePresignedURLResponse(event) {
  if (event.target.readyState == 4 && event.target.status == 200) {
    const { url } = JSON.parse(event.target.response);
    const request = new XMLHttpRequest();
    request.onreadystatechange = handleListObjectV2Response;
    request.open("GET", url, true);
    request.send();
  }
}

function onDownloadButtonClick(event) {
  const key = event.target.dataset.key;
  const request = new XMLHttpRequest();
  request.onreadystatechange = (event) => {
    const { readyState, status, response } = event.target;
    if (readyState == 4 && status == 200) {
      window.open(JSON.parse(response).url, "_blank");
    }
  };
  request.open(
    "GET",
    `/api/project/${projectId}/documents/presigned_download_url?key=${key}`,
    true
  );
  request.send();
}

function onDeleteButtonClick(event) {
  const { key } = event.target.dataset;
  if (
    !window.confirm(
      interpolate(gettext("Delete the document %s ?"), [key.split("/").pop()])
    )
  ) {
    return;
  }
  toggleLoading(true);
  new Promise((resolve, reject) => {
    const request = new XMLHttpRequest();
    request.onreadystatechange = (event) => {
      const { readyState, status, response } = event.target;
      if (readyState == 4) {
        if (status == 200) {
          const request = new XMLHttpRequest();
          request.onreadystatechange = (event) => {
            const { readyState, status } = event.target;
            if (readyState == 4) {
              if (status == 204) {
                resolve();
              } else {
                reject(event.target);
              }
            }
          };
          request.open("DELETE", JSON.parse(response).url, true);
          request.send();
        } else {
          reject(event.target);
        }
      }
    };
    request.open(
      "GET",
      `/api/project/${projectId}/documents/presigned_delete_url?key=${key}`,
      true
    );
    request.send();
  })
    .then(() => {
      fetchDocuments(projectId);
      displayMessage(
        interpolate(gettext("File %s has been removed."), [
          key.split("/").pop(),
        ]),
        "success"
      );
    })
    .catch((response) => {
      displayMessage(
        interpolate(gettext("File %s could not be removed."), [
          key.split("/").pop(),
        ]),
        "error"
      );
    });
}

function createActionCell(key) {
  const actionsEl = new DOMParser().parseFromString(
    '<ul class="fr-btns-group fr-btns-group--inline fr-btns-group--sm">\
      <li><button class="download-btn fr-btn fr-fi-download-line fr-btn--secondary"></button></li>\
      <li><button class="delete-btn fr-btn fr-fi-delete-line fr-btn--secondary"></button></li>\
      </ul>',
    "text/html"
  );
  const buttons = actionsEl.querySelectorAll("button");
  buttons[0].textContent = gettext("Download file");
  buttons[0].setAttribute("title", gettext("Download file"));
  buttons[0].setAttribute("data-key", key);
  buttons[0].addEventListener("click", onDownloadButtonClick);
  buttons[1].textContent = gettext("Delete file");
  buttons[1].setAttribute("title", gettext("Delete file"));
  buttons[1].setAttribute("title", gettext("Download file"));
  buttons[1].setAttribute("data-key", key);
  buttons[1].addEventListener("click", onDeleteButtonClick);
  return actionsEl.body.firstElementChild;
}
