import "../../../js_tests/_jsdom_mocks/gettext";
import euphrosyneToolsService from "../../assets/js/euphrosyne-tools-service";
import VirtualOfficeDeleteButton from "../../assets/js/components/virtual-office-delete-button";

import utils from "../../../assets/js/utils";

describe("Test VirtualOfficeDeleteButton", () => {
  let voDeleteButton;
  VirtualOfficeDeleteButton.init();

  beforeEach(() => {
    vi.spyOn(window, "dispatchEvent");
    vi.spyOn(euphrosyneToolsService, "deleteVM");
    vi.spyOn(utils, "displayMessage");
    vi.spyOn(window, "confirm").mockReturnValue(true);

    voDeleteButton = new VirtualOfficeDeleteButton();
    voDeleteButton.setAttribute("project-name", "projet tango");
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("creates the button properly", async () => {
    euphrosyneToolsService.deleteVM.mockImplementation(() => Promise.resolve());
    await voDeleteButton.onButtonClick();

    expect(euphrosyneToolsService.deleteVM).toHaveBeenCalled();
    expect(window.dispatchEvent).toHaveBeenLastCalledWith(
      new CustomEvent("vm-deleted"),
    );
    expect(utils.displayMessage).toHaveBeenLastCalledWith(
      "The virtual office has been deleted.",
      "success",
    );
  });

  it("handles error correctly", async () => {
    euphrosyneToolsService.deleteVM.mockImplementation(() => Promise.reject());

    let hadError = false;
    try {
      await voDeleteButton.onButtonClick();
    } catch (_) {
      hadError = true;
    }

    expect(hadError).toBe(true);
    expect(utils.displayMessage).toHaveBeenLastCalledWith(
      "An error occured while deleting the virtual office.",
      "error",
    );
  });
});
