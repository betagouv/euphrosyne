export class FileTable extends HTMLTableElement {
  constructor() {
    super();
    this.classList.add("file-table");
    this.dataRows = [];
  }

  static init() {
    customElements.define("file-table", FileTable, { extends: "table" });
  }

  showLoading() {
    this.tBodies[0].querySelectorAll("tr").forEach((row) => row.remove());
    this.tBodies[0].appendChild(this.generateLoadingRow());
  }

  displayFiles() {
    this.tBodies[0].querySelectorAll("tr").forEach((row) => row.remove());
    if (this.dataRows.length > 0) {
      this.dataRows.forEach((row) => {
        this.tBodies[0].appendChild(row);
      });
    } else {
      this.tBodies[0].appendChild(this.generateNoDataRow());
    }
  }

  setFiles(files) {
    this.dataRows = [];
    files.forEach((file) => {
      const rowEl = this.insertRow(-1);
      rowEl.classList.add("document-row");

      const keyCell = rowEl.insertCell(),
        keyCellText = document.createTextNode(file.name);
      keyCell.appendChild(keyCellText);

      const lastModifiedCell = rowEl.insertCell(),
        lastModifiedCellText = document.createTextNode(file.lastModified);
      lastModifiedCell.appendChild(lastModifiedCellText);

      const sizeCell = rowEl.insertCell(),
        sizeCellText = document.createTextNode(file.size);
      sizeCell.appendChild(sizeCellText);

      const actionsText = rowEl.insertCell();
      actionsText.appendChild(this.generateActionCellContent(file.key));
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

  generateActionCellContent(key) {
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
      "fr-fi-download-line",
      "fr-btn--secondary"
    );
    downloadButton.textContent = window.gettext("Download file");
    downloadButton.title = window.gettext("Download file");
    downloadButton.addEventListener("click", () => {
      this.dispatchEvent(
        new CustomEvent("download-click", { detail: { key } })
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
        "fr-fi-delete-line",
        "fr-btn--secondary"
      );
      deleteButton.textContent = window.gettext("Delete file");
      deleteButton.title = window.gettext("Delete file");
      deleteButton.addEventListener("click", () =>
        this.dispatchEvent(new CustomEvent("delete-click", { detail: { key } }))
      );
      const deleteListItem = document.createElement("li");
      deleteListItem.appendChild(deleteButton);
      unorderedList.appendChild(deleteListItem);
    }

    return unorderedList;
  }
}
