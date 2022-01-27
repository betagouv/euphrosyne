/* global global */
import { jest } from "@jest/globals";

import handleInitData from "../assets/js/run-popup-response-handler.js";

describe("handleInitData", () => {
  it("properly calls dismissAddRelatedRunPopup on add action", () => {
    global.opener = { dismissAddRelatedRunPopup: jest.fn() };
    handleInitData({ action: "add", data: "some data" });
    expect(global.opener.dismissAddRelatedRunPopup).toHaveBeenCalledWith(
      window,
      "some data"
    );
  });
  it("properly calls dismissChangeRelatedRunPopup on change action", () => {
    global.opener = { dismissChangeRelatedRunPopup: jest.fn() };
    handleInitData({ action: "change", data: "some data" });
    expect(global.opener.dismissChangeRelatedRunPopup).toHaveBeenCalledWith(
      window,
      "some data"
    );
  });
  it("properly calls dismissDeleteRelatedRunPopup on add action", () => {
    global.opener = { dismissDeleteRelatedRunPopup: jest.fn() };
    handleInitData({ action: "delete", value: "some id" });
    expect(global.opener.dismissDeleteRelatedRunPopup).toHaveBeenCalledWith(
      window,
      "some id"
    );
  });
});
