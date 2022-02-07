import { jest } from "@jest/globals";
import { dismissAddRelatedRunPopup } from "../assets/js/pages/run-inline.js";

// We skip these tests for now because run-inline.js relies on jquery. Ideal
// solution: remove dependency on jquery.kALjk
describe.skip("dismissAddRelatedRunPopup", () => {
  it("updates the DOM with new data", () => {
    const mockWindow = {
      close: jest.fn(),
    };
    document.body.innerHTML = `
    <div id="runs-group">
      <div id="runs">
        <div id="runs-0" class="inline-related"></div>
        <div id="runs-1" class="inline-related"></div>
        <div id="runs-empty" class="inline-related"></div>
        <div class="add-row"><a href="#">Ajouter un objet Run supplémentaire</a></div>
      </div>
    </div>`;

    const initialInlineLabelsLength = document
      .getElementById("runs-group")
      .querySelectorAll(".inline-related").length;

    dismissAddRelatedRunPopup(mockWindow, {
      id: 42,
      label: "label",
      beamline: "beamline",
    });

    expect(
      document.getElementById("runs-group").querySelectorAll(".inline-related")
        .length
    ).to.equal(initialInlineLabelsLength + 1);
  });
});
