import { FileTable } from "../../../../assets/js/components/file-table.js";

export class HDF5FileTable extends FileTable {
  constructor() {
    super();
    this.classList.add("file-table");
    this.dataRows = [];
  }

  static init() {
    customElements.define("hdf5-file-table", HDF5FileTable, {
      extends: "table",
    });
  }

  generateActionCellContent(file) {
    const { path } = file;
    const unorderedList = document.createElement("ul");
    unorderedList.classList.add(
      "fr-btns-group",
      "fr-btns-group--inline",
      "fr-btns-group--sm"
    );
    const viewLink = document.createElement("a");
    viewLink.textContent = window.gettext("View");
    viewLink.href = `lab/project/${window.projectId}/hdf5-viewer?file=${path}`;
    viewLink.target = "_blank";
    viewLink.rel = "noopener";
    const anchorListItem = document.createElement("li");
    anchorListItem.appendChild(viewLink);
    unorderedList.appendChild(anchorListItem);

    return unorderedList;
  }
}
