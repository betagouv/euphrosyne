import "../_jsdom_mocks/gettext";

import { FileTable } from "../../assets/js/components/file-table";
import { S3File } from "../../assets/js/s3-service";

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
      new S3File("path/to/object1", new Date().toLocaleDateString(), "12 KB"),
      new S3File("path/to/object2", new Date().toLocaleDateString(), "12 KB"),
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
      expect(firstObjectCells[1].textContent).toBe(files[0].lastModified);
      expect(firstObjectCells[2].textContent).toBe(files[0].size);
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
