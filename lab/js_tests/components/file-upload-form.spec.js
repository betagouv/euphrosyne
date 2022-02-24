import { jest } from "@jest/globals";

import "../_jsdom_mocks/gettext";

import { FileUploadForm } from "../../assets/js/components/file-upload-form";

describe("Test FileUploadForm", () => {
  FileUploadForm.init();

  beforeEach(() => {
    document.body.innerHTML = `
        <form is="file-upload-form">
        <input class="fr-upload" type="file" id="file-upload" name="files" multiple required>
        </table>`;
  });

  describe("Test validation", () => {
    it("accepts files if total size is less or equal to 30 Mb", () => {
      const setCustomValidityMock = jest.fn();
      const event = {
        target: {
          files: [
            { name: "1.jpg", size: 30719999 },
            { name: "2.jpg", size: 1 },
          ],
          setCustomValidity: setCustomValidityMock,
        },
      };
      document.querySelector("form").validateFileInput(event);

      expect(setCustomValidityMock).toHaveBeenCalledTimes(1);
      expect(setCustomValidityMock.mock.calls[0][0]).toBe("");
    });

    it("rejects large files", () => {
      const setCustomValidityMock = jest.fn();
      const event = {
        target: {
          files: [
            { name: "1.jpg", size: 30719999 },
            { name: "2.jpg", size: 2 },
          ],
          setCustomValidity: setCustomValidityMock,
        },
      };

      document.querySelector("form").validateFileInput(event);

      expect(setCustomValidityMock).toHaveBeenCalledTimes(2);
      expect(
        setCustomValidityMock.mock.calls[1][0].startsWith(
          "Total file sizes must not exceed"
        )
      ).toBeTruthy();
    });

    it("rejects unknown extensions", () => {
      const setCustomValidityMock = jest.fn();
      const event = {
        target: {
          files: [
            { name: "1.jpg", size: 32 },
            { name: "2.abc", size: 45 },
          ],
          setCustomValidity: setCustomValidityMock,
        },
      };

      document.querySelector("form").validateFileInput(event);

      expect(setCustomValidityMock).toHaveBeenCalledTimes(2);
      expect(
        setCustomValidityMock.mock.calls[1][0].startsWith(
          "The following file formats are not accepted"
        )
      ).toBeTruthy();
    });
  });
});
