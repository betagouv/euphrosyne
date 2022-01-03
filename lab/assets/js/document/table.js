"use strict";

import { formatBytes, displayMessage } from "../utils.js";
import { fetchDownloadPresignedURL } from "./presigned-url-service.js";
import { listObjectsV2, deleteObject } from "./s3-service.js";

export function toggleLoading(active) {
  if (active) {
    document
      .querySelectorAll("table#document_list tbody tr:not(.loading)")
      .forEach((el) => (el.style.display = "none"));
    document.querySelector(
      "table#document_list tbody tr.loading"
    ).style.display = "";
  } else {
    const tableRows = document.querySelectorAll(
      "table#document_list tbody tr:not(.loading)"
    );
    tableRows.forEach((el) => (el.style.display = ""));
    if (tableRows.length > 1) {
      document.querySelector("tr.no_data").style.display = "none";
    }
    document.querySelector(
      "table#document_list tbody tr.loading"
    ).style.display = "none";
  }
}

export async function fetchDocuments(projectId) {
  const keys = await listObjectsV2(projectId);
  displayProjectDocuments(keys);
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

async function onDownloadButtonClick(event) {
  const key = event.target.dataset.key;
  const url = await fetchDownloadPresignedURL(projectId, key);
  window.open(url, "_blank");
}

function handleDeleteError(key) {
  displayMessage(
    interpolate(gettext("File %s could not be removed."), [
      key.split("/").pop(),
    ]),
    "error"
  );
  toggleLoading(false);
}

function handleDeleteSuccess(projectId, key) {
  fetchDocuments(projectId);
  displayMessage(
    interpolate(gettext("File %s has been removed."), [key.split("/").pop()]),
    "success"
  );
}

async function onDeleteButtonClick(event) {
  const { key } = event.target.dataset;
  if (
    !window.confirm(
      interpolate(gettext("Delete the document %s ?"), [key.split("/").pop()])
    )
  ) {
    return;
  }
  toggleLoading(true);
  try {
    await deleteObject(projectId, key);
    handleDeleteSuccess(projectId, key);
  } catch (error) {
    handleDeleteError(key);
    return;
  }
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
