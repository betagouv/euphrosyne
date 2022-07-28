import "../_jsdom_mocks/gettext";

import { FileTable } from "../../assets/js/components/file-table";
import { EuphrosyneFile } from "../../assets/js/file-service";
import { formatBytes } from "../../assets/js/utils";

describe("Test FileTable", () => {
  FileTable.init();

  beforeEach(() => {
    document.body.innerHTML = `
        <table is="file-table">
            <thead>
                <tr>  
                    <th scope="col" class="column-name">1</th>
                    <th scope="col" class="column-name">2</th>
                    <th scope="col" class="column-name">3</th>
                </tr>
            </thead>
            <tbody>
            </tbody>
        </table>`;
  });

  describe("Test show loading", () => {
    it("shows a loading row with one td for every th", () => {
      document.querySelector("table").showLoading();
      expect(document.querySelector("tbody tr.loading")).toBeTruthy();
      expect(document.querySelectorAll("tbody tr.loading td").length).toBe(3);
    });
  });

  describe("Test file display", () => {
    const files = [
      new EuphrosyneFile("file-1.txt", "path/to/file-1.txt", new Date(), 12000),
      new EuphrosyneFile("file-2.txt", "path/to/file-2.txt", new Date(), 12000),
    ];
    it("shows files in tbody", () => {
      const table = document.querySelector("table");
      table.setFiles(files);
      table.displayFiles();
      const fileRows = document.querySelectorAll(".document-row");
      const firstObjectCells = fileRows[0].querySelectorAll("td");
      expect(fileRows.length).toBe(2);
      expect(firstObjectCells.length).toBe(4);
      expect(firstObjectCells[0].textContent).toBe(files[0].name);
      expect(firstObjectCells[1].textContent).toBe(
        files[0].lastModified.toLocaleDateString()
      );
      expect(firstObjectCells[2].textContent).toBe(formatBytes(files[0].size));
      expect(
        firstObjectCells[3].querySelectorAll("button.download-btn").length
      ).toBe(1);
    });

    it("does not show delete button by default", () => {
      const table = document.querySelector("table");
      table.setFiles(files);
      table.displayFiles();
      expect(document.querySelectorAll("button.delete-btn").length).toBe(0);
    });

    it("adds a delete button if can-delete is specified", () => {
      const table = document.querySelector("table");
      table.dataset.canDelete = true;
      table.setFiles(files);
      table.displayFiles();
      expect(document.querySelectorAll("button.delete-btn").length).toBe(2);
    });

    it("adds a specific row when no file", () => {
      const table = document.querySelector("table");
      table.setFiles([]);
      table.displayFiles();
      const noDataRow = document.querySelector("tr.no_data");
      expect(noDataRow).toBeTruthy();
      expect(noDataRow.textContent).toBe("No file yet");
      expect(noDataRow.querySelector("td").getAttribute("colspan")).toBe("3");
    });
  });
});
