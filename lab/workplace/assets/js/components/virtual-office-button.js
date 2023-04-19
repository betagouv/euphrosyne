"use strict";

import euphrosyneToolsService from "../euphrosyne-tools-service.js";
import utils from "../../../../assets/js/utils.js";

export default class VirtualOfficeButton extends HTMLButtonElement {
  static init() {
    customElements.define("virtual-office-button", VirtualOfficeButton, {
      extends: "button",
    });
  }

  get projectSlug() {
    return this.getAttribute("project-slug");
  }

  constructor() {
    super();
    this.addEventListener("click", this.onButtonClick);
    window.addEventListener("vm-deleted", () => {
      this.disabled = false;
      this.innerText = window.gettext("Create virtual office");
      this.connectionUrl = null;
    });
  }

  connectedCallback() {
    this.disabled = true;
    this.initButton();
  }

  async onButtonClick() {
    if (this.connectionUrl) {
      window.open(this.connectionUrl, "_blank");
    } else {
      this.disabled = true;
      try {
        await euphrosyneToolsService.deployVM(this.projectSlug);
      } catch (error) {
        this.disabled = false;
        utils.displayMessage(
          window.gettext(
            "An error occured while creating the virtual office. Please contact an administrator or try again later."
          ),
          "error"
        );
        throw error;
      }
      utils.displayMessage(
        window.gettext(
          "The virtual office is being created. This can take up to 10 minutes."
        ),
        "success"
      );
      this.waitForDeploymentComplete();
    }
  }

  waitForDeploymentComplete() {
    this.innerText = window.gettext("Creating virtual office...");
    this.checkDeploymentProgress();
    this.checkDeploymentIntervalId = setInterval(
      this.checkDeploymentProgress.bind(this),
      7000
    );
  }

  async initButton() {
    const url = await euphrosyneToolsService.fetchVMConnectionLink(
      this.projectSlug
    );
    if (url) {
      this.connectionUrl = url;
      this.disabled = false;
      this.onConnectReady();
    } else {
      const deploymentStatus =
        await euphrosyneToolsService.fetchDeploymentStatus(this.projectSlug);
      if (deploymentStatus) {
        this.deploymentStatus = deploymentStatus;
        if (deploymentStatus === "Failed") {
          this.onFailedDeployment();
        } else {
          this.waitForDeploymentComplete();
        }
      } else {
        this.disabled = false;
        this.innerText = window.gettext("Create virtual office");
      }
    }
  }

  async checkDeploymentProgress() {
    if (this.deploymentStatus && this.deploymentStatus === "Succeeded") {
      const url = await euphrosyneToolsService.fetchVMConnectionLink(
        this.projectSlug
      );
      if (url) {
        this.connectionUrl = url;
        clearInterval(this.checkDeploymentIntervalId);
        this.checkDeploymentIntervalId = null;
        this.disabled = false;
        this.innerText = window.gettext("Access virtual office");
        utils.displayMessage(
          window.gettext(
            "The virtual office is ready. You can now access it by clicking Access virtual office button."
          ),
          "success"
        );
        this.onConnectReady();
      }
    } else {
      const deploymentStatus =
        await euphrosyneToolsService.fetchDeploymentStatus(this.projectSlug);
      if (deploymentStatus) {
        this.deploymentStatus = deploymentStatus;
        if (this.deploymentStatus === "Failed") {
          this.onFailedDeployment();
          clearInterval(this.checkDeploymentIntervalId);
          this.checkDeploymentIntervalId = null;
        }
      }
    }
  }

  onFailedDeployment() {
    this.innerText = window.gettext("Access virtual office");
    utils.displayMessage(
      window.gettext(
        "We could not create the virtual office. Please contact an administrator."
      ),
      "error"
    );
  }

  onConnectReady() {
    /** Sends an event so other components know virtual office is ready */
    window.dispatchEvent(new CustomEvent("vm-ready"));
  }
}
