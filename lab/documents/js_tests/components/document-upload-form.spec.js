import { jest } from "@jest/globals";

import "../../../js_tests/_jsdom_mocks/gettext";

import { DocumentUploadForm } from "../../assets/js/components/document-upload-form";

describe("Test DocumentUploadForm", () => {
  DocumentUploadForm.init();

  beforeEach(() => {
    document.body.innerHTML = `
        <form is="document-upload-form">
        <input class="fr-upload" type="file" id="file-upload" name="files" multiple required>
        </table>`;
  });

  describe("Test validation", () => {
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
