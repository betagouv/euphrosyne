"use strict";

import euphrosyneToolsService from "../euphrosyne-tools-service.js";
import utils from "../../../../assets/js/utils.js";
import euphrosyneToolsFetch from "../../../../../shared/js/euphrosyne-tools-client.ts";

export default class VirtualOfficeButton extends HTMLElement {
  connectionUrl = null;
  buttonEl = null;

  static init() {
    customElements.define("virtual-office-button", VirtualOfficeButton);
  }

  get projectSlug() {
    return this.getAttribute("project-slug");
  }

  constructor() {
    super();
    this.createButton();
    this.buttonEl = this.querySelector("button");
    this.buttonEl.addEventListener(
      "click",
      function () {
        this.onButtonClick();
      }.bind(this),
      false,
    );
    this.fetchFn = euphrosyneToolsFetch;
    window.addEventListener("vm-deleted", () => {
      this.buttonEl.disabled = false;
      this.buttonEl.innerText = window.gettext("Create virtual office");
      this.connectionUrl = null;
    });
  }

  connectedCallback() {
    this.buttonEl.disabled = true;
    this.initButton();
  }

  async onButtonClick() {
    if (this.connectionUrl) {
      window.open(this.connectionUrl, "_blank");
    } else {
      this.buttonEl.disabled = true;
      try {
        await euphrosyneToolsService.deployVM(this.projectSlug, this.fetchFn);
      } catch (error) {
        this.buttonEl.disabled = false;
        utils.displayMessage(
          window.gettext(
            "An error occured while creating the virtual office. Please contact an administrator or try again later.",
          ),
          "error",
        );
        throw error;
      }
      utils.displayMessage(
        window.gettext(
          "The virtual office is being created. This can take up to 10 minutes.",
        ),
        "info",
      );
      this.buttonEl.innerText = window.gettext("Creating virtual office...");
      setTimeout(() => this.waitForDeploymentComplete(), 10000); // Wait 10 seconds before checking deployment status
    }
  }

  waitForDeploymentComplete() {
    this.checkDeploymentProgress();
    this.checkDeploymentIntervalId = setInterval(
      this.checkDeploymentProgress.bind(this),
      10000,
    );
  }

  async initButton() {
    const url = await euphrosyneToolsService.fetchVMConnectionLink(
      this.projectSlug,
      this.fetchFn,
    );
    if (url) {
      this.connectionUrl = url;
      this.buttonEl.disabled = false;
      this.onConnectReady();
    } else {
      const deploymentStatus =
        await euphrosyneToolsService.fetchDeploymentStatus(
          this.projectSlug,
          this.fetchFn,
        );
      if (deploymentStatus) {
        this.deploymentStatus = deploymentStatus;
        if (deploymentStatus === "Failed") {
          this.onFailedDeployment();
        } else {
          this.buttonEl.innerText = window.gettext(
            "Creating virtual office...",
          );
          utils.displayMessage(
            window.gettext(
              "The virtual office is being created. This can take up to 10 minutes.",
            ),
            "info",
          );
          this.waitForDeploymentComplete();
        }
      } else {
        this.buttonEl.disabled = false;
        this.buttonEl.innerText = window.gettext("Create virtual office");
      }
    }
  }

  async checkDeploymentProgress() {
    const deploymentStatus = await euphrosyneToolsService.fetchDeploymentStatus(
      this.projectSlug,
      this.fetchFn,
    );
    if (deploymentStatus === "Failed") {
      this.onFailedDeployment();
      clearInterval(this.checkDeploymentIntervalId);
      this.checkDeploymentIntervalId = null;
    } else if (!deploymentStatus | (deploymentStatus === "Succeeded")) {
      utils.displayMessage(
        window.gettext(
          "The virtual machine has been deployed and is being configured.",
        ),
        "info",
      );
      clearInterval(this.checkDeploymentIntervalId);
      this.checkDeploymentIntervalId = null;
      this.checkConnectionLinkIntervalId = setInterval(
        () => this.waitForConnectionLink(),
        10000,
      );
      setTimeout(
        () => this.reportNoConnectionLinkTimeoutError(),
        2 * 60 * 1000,
      ); // Wait 3 minutes before reporting a timeout error
    }
  }

  async waitForConnectionLink() {
    const url = await euphrosyneToolsService.fetchVMConnectionLink(
      this.projectSlug,
      this.fetchFn,
    );
    if (url) {
      this.connectionUrl = url;
      clearInterval(this.checkConnectionLinkIntervalId);
      this.checkConnectionLinkIntervalId = null;
      this.buttonEl.disabled = false;
      this.buttonEl.innerText = window.gettext("Access virtual office");
      utils.displayMessage(
        window.gettext(
          "The virtual office is ready. You can now access it by clicking Access virtual office button.",
        ),
        "success",
      );
      this.onConnectReady();
    }
  }

  async reportNoConnectionLinkTimeoutError() {
    if (!this.connectionUrl) {
      clearInterval(this.checkConnectionLinkIntervalId);
      this.checkConnectionLinkIntervalId = null;
      this.buttonEl.disabled = false;
      this.buttonEl.innerText = window.gettext("Create virtual office");
      utils.displayMessage(
        window.gettext(
          "Configuration took too long. Something wrong occured. Please contact an administrator.",
        ),
        "error",
      );
    }
  }

  onFailedDeployment() {
    this.buttonEl.innerText = window.gettext("Access virtual office");
    utils.displayMessage(
      window.gettext(
        "We could not create the virtual office. Please contact an administrator.",
      ),
      "error",
    );
  }

  onConnectReady() {
    /** Sends an event so other components know virtual office is ready */
    window.dispatchEvent(new CustomEvent("vm-ready"));
  }

  createButton() {
    const button = document.createElement("button");
    button.classList.add(
      ...["fr-btn", "fr-icon-arrow-right-line", "fr-btn--icon-right"],
    );
    button.innerText = window.gettext("Access virtual office");
    this.appendChild(button);
  }
}
