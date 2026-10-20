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
      3,
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

describe("Formset row escaping", () => {
  it("renders object representations as text without creating HTML", () => {
    const representation =
      '<img src=x onerror=alert(1)> & "quotes" {{ objectId }}';
    const row = loadFormsetRow(
      "objects",
      1,
      2,
      "objectgroup",
      "/lab/objectgroup/2/change/",
      representation,
      "run",
      3,
    );

    expect(row.querySelector("a").textContent).toBe(representation);
    expect(row.querySelector("img, script, [onerror]")).toBeNull();
    expect(row.querySelector("a").getAttribute("href")).toBe(
      "/lab/objectgroup/2/change/",
    );
    expect(row.querySelector('input[name="objects-1-id"]').value).toBe("2");
    expect(row.querySelector('input[name="objects-1-run"]').value).toBe("3");
    expect(row.querySelector('input[type="checkbox"]').name).toBe(
      "objects-1-DELETE",
    );
  });
});
