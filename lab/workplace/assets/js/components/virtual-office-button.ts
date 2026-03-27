"use strict";

import euphrosyneToolsService from "../euphrosyne-tools-service.js";
import utils from "../../../../assets/js/utils.js";
import euphrosyneToolsFetch from "../../../../../shared/js/euphrosyne-tools-client";

type DeploymentStatus =
  | "NotSpecified"
  | "Accepted"
  | "Running"
  | "Ready"
  | "Creating"
  | "Created"
  | "Canceled"
  | "Failed"
  | "Succeeded"
  | "Updating";

export default class VirtualOfficeButton extends HTMLElement {
  connectionUrl: string | null = null;
  buttonEl: HTMLButtonElement;
  fetchFn: typeof fetch = euphrosyneToolsFetch;

  deploymentStatus: DeploymentStatus | null = null;

  checkDeploymentIntervalId?: number;
  checkDeletingIntervalId?: number;
  checkConnectionLinkIntervalId?: number;

  static init() {
    customElements.define("virtual-office-button", VirtualOfficeButton);
  }

  get projectSlug() {
    return this.getAttribute("project-slug");
  }

  get canStartVm() {
    const canStart = this.getAttribute("can-start-vm") || "true";
    return canStart === "true";
  }

  constructor() {
    super();
    this.createButton();
    const buttonEl = this.querySelector("button");
    if (!buttonEl) {
      throw new Error(
        "virtual office button component must have a button element inside.",
      );
    }
    this.buttonEl = buttonEl;

    this.buttonEl.addEventListener(
      "click",
      () => {
        this.onButtonClick();
      },
      false,
    );

    window.addEventListener("vm-deleted", () => {
      this.buttonEl.disabled = false;
      this.buttonEl.innerText = window.gettext("Create virtual office");
      this.connectionUrl = null;
    });
  }

  connectedCallback() {
    this.disableButton();
    this.initButton();
  }

  async onButtonClick() {
    if (this.connectionUrl) {
      window.open(this.connectionUrl, "_blank");
    } else {
      this.disableButton();
      try {
        await euphrosyneToolsService.deployVM(this.projectSlug, this.fetchFn);
      } catch (error) {
        this.enableButton();
        utils.displayMessage(
          window.gettext(
            "An error occurred while creating the virtual office. Please contact an administrator or try again later.",
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
    this.checkDeploymentIntervalId = window.setInterval(
      this.checkDeploymentProgress.bind(this),
      10000,
    );
  }

  enableButton() {
    this.buttonEl.disabled = false;
  }

  disableButton() {
    this.buttonEl.disabled = true;
  }

  async initButton() {
    if (!this.canStartVm) {
      return;
    }
    const vmStatus = await euphrosyneToolsService.fetchVMProvisioningState(
      this.projectSlug,
      this.fetchFn,
    );
    if (vmStatus === "Deleting") {
      this.disableButton();
      this.buttonEl.innerText = window.gettext("Deleting virtual office...");
      this.checkDeletingIntervalId = window.setInterval(
        () => this.checkDeletingProgress(),
        10000,
      );
    } else {
      const url = await euphrosyneToolsService.fetchVMConnectionLink(
        this.projectSlug,
        this.fetchFn,
      );
      if (url) {
        this.connectionUrl = url;
        this.enableButton();
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
          this.enableButton();
          this.buttonEl.innerText = window.gettext("Create virtual office");
        }
      }
    }
  }

  async checkDeploymentProgress() {
    const deploymentStatus =
      (await euphrosyneToolsService.fetchDeploymentStatus(
        this.projectSlug,
        this.fetchFn,
      )) as DeploymentStatus | null;
    if (deploymentStatus === "Failed") {
      this.onFailedDeployment();
      clearInterval(this.checkDeploymentIntervalId);
      this.checkDeploymentIntervalId = undefined;
    } else if (!deploymentStatus || deploymentStatus === "Succeeded") {
      utils.displayMessage(
        window.gettext(
          "The virtual machine has been deployed and is being configured.",
        ),
        "info",
      );
      clearInterval(this.checkDeploymentIntervalId);
      this.checkDeploymentIntervalId = undefined;
      this.checkConnectionLinkIntervalId = window.setInterval(
        () => this.waitForConnectionLink(),
        10000,
      );
      setTimeout(
        () => this.reportNoConnectionLinkTimeoutError(),
        2 * 60 * 1000,
      ); // Wait 3 minutes before reporting a timeout error
    }
  }

  async checkDeletingProgress() {
    const vmStatus = await euphrosyneToolsService.fetchVMProvisioningState(
      this.projectSlug,
      this.fetchFn,
    );
    if (!vmStatus) {
      this.enableButton();
      this.buttonEl.innerText = window.gettext("Create virtual office");
      clearInterval(this.checkDeletingIntervalId);
      this.checkDeletingIntervalId = undefined;
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
      this.checkConnectionLinkIntervalId = undefined;
      this.enableButton();
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
      this.checkConnectionLinkIntervalId = undefined;
      this.enableButton();
      this.buttonEl.innerText = window.gettext("Create virtual office");
      utils.displayMessage(
        window.gettext(
          "Configuration took too long. Something wrong occurred. Please contact an administrator.",
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
