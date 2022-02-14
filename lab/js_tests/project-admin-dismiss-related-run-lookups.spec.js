import { jest } from "@jest/globals";
import {
  dismissChangeRelatedRunPopup,
  dismissDeleteRelatedRunPopup,
} from "../assets/js/run-inline-handlers.js";

import template from "./project-admin-runs.html";

describe("dismissChangeRelatedRunPopup", () => {
  it("updates the indexes", () => {
    const mockWindow = {
      close: jest.fn(),
    };
    document.body.innerHTML = template;

    dismissChangeRelatedRunPopup(mockWindow, {
      id: "92",
      label: "new label",
      beamline: "new beamline",
    });

    expect(document.querySelector(".label-test-class").textContent).toMatch(
      /^new label/
    );
    expect(document.querySelector(".beamline-test-class").textContent).toMatch(
      /^\s*new beamline\s*$/
    );
  });
});

describe("dismissDeleteRelatedRunPopup", () => {
  it("removes the div", () => {
    const mockWindow = {
      close: jest.fn(),
    };
    document.body.innerHTML = template;

    const initialInlineLabelsLength = document
      .getElementById("runs-group")
      .querySelectorAll(".inline-related").length;

    dismissDeleteRelatedRunPopup(mockWindow, "95");

    expect(
      document.getElementById("runs-group").querySelectorAll(".inline-related")
        .length
    ).toEqual(initialInlineLabelsLength - 1);

    expect(
      Array.from(document.querySelectorAll(".inline-related")).map((e) => e.id)
    ).toEqual(["runs-0", "runs-empty"]);
  });
  it("updates the indexes", () => {
    const mockWindow = {
      close: jest.fn(),
    };
    document.body.innerHTML = template;

    const initialInlineLabelsLength = document
      .getElementById("runs-group")
      .querySelectorAll(".inline-related").length;

    dismissDeleteRelatedRunPopup(mockWindow, "92");

    expect(
      document.getElementById("runs-group").querySelectorAll(".inline-related")
        .length
    ).toEqual(initialInlineLabelsLength - 1);

    expect(
      Array.from(document.querySelectorAll(".inline-related")).map((e) => e.id)
    ).toEqual(["runs-0", "runs-empty"]);
  });
});
