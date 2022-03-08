"use-strict";
import { jest } from "@jest/globals";
import { dismissAddRelatedObjectGroupPopup } from "../assets/js/objectgroup-inline-handlers.js";
import template from "./objectgroup-inline.html";

describe("Test dismissAddRelatedObjectGroupPopup", function () {
  const windowMock = {
    name: "id_Run_run_object_groups-0-objectgroup__0",
    close: jest.fn(),
  };
  it("replaces select tag by a tr", function () {
    document.body.innerHTML = template;
    dismissAddRelatedObjectGroupPopup(windowMock, 2, "A beautifull object", [
      [3, 1],
    ]);
    expect(document.getElementById("Run_run_object_groups-0")).toBeTruthy();
    expect(document.getElementById("Run_run_object_groups-0").tagName).toBe(
      "TR"
    );
  });

  it("updates initial form input", function () {
    document.body.innerHTML = template;
    dismissAddRelatedObjectGroupPopup(windowMock, 2, "A beautifull object", [
      [3, 1],
    ]);
    expect(
      document.querySelector(
        "input[name='Run_run_object_groups-INITIAL_FORMS']"
      ).value
    ).toBe("1");
  });

  it("closes the popup", function () {
    windowMock.close.mockClear();
    document.body.innerHTML = template;
    dismissAddRelatedObjectGroupPopup(windowMock, 2, "A beautifull object", [
      [3, 1],
    ]);
    expect(windowMock.close).toHaveBeenCalled();
  });

  it("calls dismissAddRelatedObjectPopup when current run is not in array", function () {
    document.body.innerHTML = template;
    window.dismissAddRelatedObjectPopup = jest.fn();
    dismissAddRelatedObjectGroupPopup(windowMock, 2, "A beautifull object", [
      [3, 4],
    ]);
    expect(window.dismissAddRelatedObjectPopup).toHaveBeenCalled();
  });
});
