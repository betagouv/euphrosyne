import { getFileInputCustomValidity } from "../assets/js/document-upload-form";

Object.defineProperty(window, "gettext", {
  value: (str: string) => str,
});

Object.defineProperty(window, "interpolate", {
  value: (str: string) => str,
});

describe("Test getFileInputCustomValidity", () => {
  describe("Test validation", () => {
    it("rejects empty file list", () => {
      expect(getFileInputCustomValidity(null)).toBe("Please select a file");
      expect(getFileInputCustomValidity([])).toBe("Please select a file");
    });

    it("rejects unsupported file formats", () => {
      const invalidFile = new File([""], "test.awrongformat");
      expect(getFileInputCustomValidity([invalidFile])).toBe(
        "The following file formats are not accepted : %s"
      );
    });

    it("accepts supported file formats", () => {
      const validFile = new File([""], "test.csv");
      expect(getFileInputCustomValidity([validFile])).toBe("");
    });
  });
});
