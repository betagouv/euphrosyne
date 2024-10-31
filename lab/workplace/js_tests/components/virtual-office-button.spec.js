import "../../../js_tests/_jsdom_mocks/gettext";
import euphrosyneToolsService from "../../assets/js/euphrosyne-tools-service";
import VirtualOfficeButton from "../../assets/js/components/virtual-office-button";

import utils from "../../../assets/js/utils";

describe("Test VirtualOfficeButton", () => {
  let voButton, fetchVMMock, fetchDeploymentMock;
  VirtualOfficeButton.init();

  beforeEach(() => {
    fetchVMMock = vi.spyOn(euphrosyneToolsService, "fetchVMConnectionLink");
    fetchDeploymentMock = vi.spyOn(
      euphrosyneToolsService,
      "fetchDeploymentStatus",
    );
    vi.spyOn(utils, "displayMessage");

    voButton = new VirtualOfficeButton();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe("Button init", () => {
    describe("When receiving connection URL directly", () => {
      beforeEach(() => {
        voButton.setAttribute("project-slug", "projet-tango");
        fetchVMMock.mockResolvedValueOnce("url");
      });
      it("creates the button properly", async () => {
        await voButton.initButton();
        expect(voButton.projectSlug).toBe("projet-tango");
        expect(voButton.connectionUrl).toBe("url");
        expect(voButton.disabled).toBeFalsy();
      });
    });

    describe("When receiving deployment status", () => {
      beforeEach(() => {
        fetchVMMock.mockResolvedValue(false);
      });

      it("wait for deploy if it has not failed", async () => {
        vi.spyOn(
          VirtualOfficeButton.prototype,
          "waitForDeploymentComplete",
        ).mockImplementation(() => Promise.resolve());
        fetchDeploymentMock.mockResolvedValueOnce("Running");
        await voButton.initButton();

        expect(voButton.waitForDeploymentComplete).toHaveBeenCalled();

        VirtualOfficeButton.prototype.waitForDeploymentComplete.mockRestore();
      });
      it("calls failed deployment callback otherwise", async () => {
        vi.spyOn(VirtualOfficeButton.prototype, "onFailedDeployment");
        fetchDeploymentMock.mockResolvedValueOnce("Failed");
        await voButton.initButton();

        expect(voButton.onFailedDeployment).toHaveBeenCalled();

        VirtualOfficeButton.prototype.onFailedDeployment.mockRestore();
      });
    });
  });

  describe("checking for deployment progress", () => {
    it("fetches connection URL when deployment has succeeded", async () => {
      fetchDeploymentMock = vi
        .spyOn(euphrosyneToolsService, "fetchDeploymentStatus")
        .mockImplementation(() => Promise.resolve("Succeeded"));
      fetchVMMock.mockImplementationOnce(() => Promise.resolve("url"));

      voButton.deploymentStatus = "Succeeded";
      fetchVMMock.mockResolvedValueOnce("url");

      vi.useFakeTimers();
      await voButton.checkDeploymentProgress();
      vi.advanceTimersByTime(10000);
      vi.useRealTimers();

      expect(fetchVMMock).toHaveBeenCalledTimes(1);
      expect(voButton.disabled).toBeFalsy();
      expect(voButton.checkDeploymentIntervalId).toBeNull();
    });

    it("handles failed deployment correctly", async () => {
      vi.spyOn(
        VirtualOfficeButton.prototype,
        "onFailedDeployment",
      ).mockImplementation(() => {});
      const clearIntervalSpy = vi.spyOn(global, "clearInterval");
      voButton.deploymentStatus = "Failed";
      fetchDeploymentMock.mockResolvedValueOnce("Failed");
      await voButton.checkDeploymentProgress();

      expect(voButton.onFailedDeployment).toHaveBeenCalledTimes(1);
      expect(voButton.checkDeploymentIntervalId).toBeNull();
      expect(clearIntervalSpy).toHaveBeenCalledTimes(1);

      VirtualOfficeButton.prototype.onFailedDeployment.mockRestore();
    });
  });

  describe("clicking on button", () => {
    vi.stubGlobal("open", vi.fn());

    it("opens a new window on click when connection url is set", async () => {
      voButton.connectionUrl = "url";
      const openSpy = vi.spyOn(window, "open");
      voButton.click();
      expect(openSpy).toHaveBeenCalledWith("url", "_blank");
    });

    it("deploys otherwise [success]", async () => {
      const deployMock = vi
        .spyOn(euphrosyneToolsService, "deployVM")
        .mockImplementationOnce(() => Promise.resolve());

      voButton.setAttribute("project-slug", "projet-tango");
      await voButton.onButtonClick();

      expect(deployMock).toHaveBeenCalledWith("projet-tango");
      expect(voButton.disabled).toBe(true);
    });

    it("waits and then fetch deployment status", () => {
      const waitDeployMock = vi
        .spyOn(VirtualOfficeButton.prototype, "waitForDeploymentComplete")
        .mockImplementationOnce(() => {});
      voButton.setAttribute("project-slug", "projet-tango");

      expect(waitDeployMock).toHaveBeenCalledTimes(0);
      vi.useFakeTimers();
      vi.advanceTimersByTime(10000);
      expect(waitDeployMock).toHaveBeenCalledTimes(0);

      VirtualOfficeButton.prototype.waitForDeploymentComplete.mockRestore();
    });

    it("deploys otherwise [failure]", async () => {
      const deployMock = vi
        .spyOn(euphrosyneToolsService, "deployVM")
        .mockImplementationOnce(() => Promise.reject());
      voButton.setAttribute("project-slug", "projet-tango");

      let hadError = false;
      try {
        await voButton.onButtonClick();
      } catch {
        hadError = true;
      }

      expect(hadError).toBe(true);
      expect(voButton.disabled).toBe(false);

      deployMock.mockRestore();
    });
  });

  describe("on deployment failure", () => {
    it("reset button and display an error message", () => {
      voButton.onFailedDeployment();

      expect(voButton.innerText).toBe("Access virtual office");
      expect(utils.displayMessage).toHaveBeenNthCalledWith(
        1,
        "We could not create the virtual office. Please contact an administrator.",
        "error",
      );
    });
  });

  describe("waiting for deployment complete", () => {
    it("reset button and display an error message", () => {
      vi.spyOn(
        VirtualOfficeButton.prototype,
        "checkDeploymentProgress",
      ).mockImplementation(() => Promise.resolve());
      vi.useFakeTimers();
      voButton.waitForDeploymentComplete();

      expect(voButton.checkDeploymentProgress).toHaveBeenNthCalledWith(1);
      expect(voButton.checkDeploymentIntervalId).toBeTruthy();

      vi.advanceTimersByTime(22000);
      expect(voButton.checkDeploymentProgress).toHaveBeenNthCalledWith(2);
      vi.useRealTimers();
    });
  });

  describe("when receiving delete event", () => {
    it("reset the button", () => {
      voButton.disabled = true;
      voButton.innerText = "Another text";
      voButton.connectionUrl = "url";

      window.dispatchEvent(new CustomEvent("vm-deleted"));

      expect(voButton.disabled).toBe(false);
      expect(voButton.innerText).toBe("Create virtual office");
      expect(voButton.connectionUrl).toBeNull();
    });
  });
});
