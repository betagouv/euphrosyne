import { formatBytes } from "../utils.js";

const COLLAPSED_ROW_NUM = 25;

export class FileTable extends HTMLTableElement {
  constructor() {
    super();
    this.classList.add("file-table");
    this.dataRows = [];
  }

  static init() {
    customElements.define("file-table", FileTable, { extends: "table" });
  }

  get cols() {
    return (this.getAttribute("cols") || "name,lastModified,size,").split(",");
  }

  showLoading() {
    this.tBodies[0].querySelectorAll("tr").forEach((row) => row.remove());
    this.tBodies[0].appendChild(this.generateLoadingRow());
  }

  displayFiles(isExpanded = false) {
    this.tBodies[0].querySelectorAll("tr").forEach((row) => row.remove());
    if (this.dataRows.length > 0) {
      this.dataRows.forEach((row, index) => {
        if (!isExpanded && index >= COLLAPSED_ROW_NUM) {
          return;
        }
        this.tBodies[0].appendChild(row);
      });
    } else {
      this.tBodies[0].appendChild(this.generateNoDataRow());
    }
    this.generateFooter(isExpanded);
  }

  setFiles(files) {
    this.dataRows = [];
    files.forEach((file) => {
      const rowEl = this.insertRow(-1);
      rowEl.classList.add("document-row");

      if (this.cols.includes("name")) {
        const nameCell = rowEl.insertCell(),
          nameCellText = document.createTextNode(file.name);
        nameCell.appendChild(nameCellText);
        nameCell.classList.add("file-name-cell");
      }

      if (this.cols.includes("lastModified")) {
        const lastModifiedCell = rowEl.insertCell(),
          lastModifiedCellText = document.createTextNode(
            file.lastModified.toLocaleDateString()
          );
        lastModifiedCell.appendChild(lastModifiedCellText);
      }

      if (this.cols.includes("size")) {
        const sizeCell = rowEl.insertCell(),
          sizeCellText = document.createTextNode(formatBytes(file.size));
        sizeCell.appendChild(sizeCellText);
      }

      const actionsText = rowEl.insertCell();
      actionsText.appendChild(this.generateActionCellContent(file));
      this.dataRows.push(rowEl);
    });
  }

  generateLoadingRow() {
    const row = document.createElement("tr");
    row.classList.add("loading");
    this.tHead.querySelectorAll("th").forEach(() => {
      const cell = document.createElement("td");
      const div = document.createElement("div");
      div.innerHTML = "&nbsp;";
      cell.appendChild(div);
      row.appendChild(cell);
    });
    return row;
  }

  generateNoDataRow() {
    const cell = document.createElement("td");
    cell.textContent = window.gettext("No file yet");
    cell.setAttribute("colspan", this.tHead.querySelectorAll("th").length);
    const row = document.createElement("tr");
    row.classList.add("no_data");
    row.appendChild(cell);
    return row;
  }

  generateActionCellContent(file) {
    const { name, path } = file;
    const unorderedList = document.createElement("ul");
    unorderedList.classList.add(
      "fr-btns-group",
      "fr-btns-group--inline",
      "fr-btns-group--sm"
    );
    const downloadButton = document.createElement("button");
    downloadButton.classList.add(
      "download-btn",
      "fr-btn",
      "fr-icon-download-line",
      "fr-btn--secondary"
    );
    downloadButton.textContent = window.gettext("Download file");
    downloadButton.title = window.gettext("Download file");
    downloadButton.addEventListener("click", () => {
      this.dispatchEvent(
        new CustomEvent("download-click", { detail: { path } })
      );
    });
    const downloadListItem = document.createElement("li");
    downloadListItem.appendChild(downloadButton);
    unorderedList.appendChild(downloadListItem);

    if (this.dataset.canDelete === "true") {
      const deleteButton = document.createElement("button");
      deleteButton.classList.add(
        "delete-btn",
        "fr-btn",
        "fr-icon-delete-line",
        "fr-btn--secondary"
      );
      deleteButton.textContent = window.gettext("Delete file");
      deleteButton.title = window.gettext("Delete file");
      deleteButton.addEventListener("click", () =>
        this.dispatchEvent(
          new CustomEvent("delete-click", { detail: { name, path } })
        )
      );
      const deleteListItem = document.createElement("li");
      deleteListItem.appendChild(deleteButton);
      unorderedList.appendChild(deleteListItem);
    }

    return unorderedList;
  }

  generateFooter(isExpanded = false) {
    if (this.querySelector("tfoot")) {
      this.querySelector("tfoot").remove();
    }
    if (this.dataRows.length <= COLLAPSED_ROW_NUM) {
      return;
    }
    const tfoot = document.createElement("tfoot");
    const row = document.createElement("tr");
    const cell = document.createElement("td");
    cell.setAttribute("colspan", this.tHead.querySelectorAll("th").length);
    cell.style = "width: 100%";
    const expandButton = document.createElement("button");
    expandButton.classList.add(
      "fr-btn",
      "fr-btn--tertiary-no-outline",
      "fr-btn--sm",
      "fr-btn--icon-left",
      isExpanded ? "fr-icon-arrow-up-s-line" : "fr-icon-arrow-down-s-line"
    );
    expandButton.innerText = isExpanded
      ? window.gettext("Show less")
      : window.gettext("Show more") + ` (${this.dataRows.length})`;
    expandButton.style.justifyContent = "center";
    expandButton.style.width = "100%";
    expandButton.ariaExpanded = isExpanded;
    expandButton.addEventListener("click", () => {
      expandButton.ariaExpanded = !isExpanded;
      this.displayFiles(!isExpanded);
    });
    cell.appendChild(expandButton);
    row.appendChild(cell);
    tfoot.appendChild(row);
    this.appendChild(tfoot);
  }
}
