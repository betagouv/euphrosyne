import { loadFormsetRow } from "../assets/js/snippet.js";

describe("Test snippet.js", function () {
  describe("Test loadFormsetRow", function () {
    const template = loadFormsetRow(
      "prefixabc",
      1,
      2,
      "objectname",
      "https://url.test",
      "A nice object",
      "Jacqueline",
      3
    );

    it("renders a tr tag", function () {
      expect(template.tagName).toBe("TR");
    });
    it("interpolates every string betweens curly brackets", function () {
      const regex = /{{[a-zA-Z_\-\s]+}}/g;
      expect(template.innerHTML.match(regex)).toBe(null);
    });
  });
});
