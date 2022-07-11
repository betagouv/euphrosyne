"use strict";

import {
  fetchVMConnectionLink,
  fetchDeploymentStatus,
  deployVM,
} from "../euphrosyne-tools-service.js";
import { displayMessage } from "../../../../assets/js/utils.js";

export class VirtualOfficeButton extends HTMLButtonElement {
  static init() {
    customElements.define("virtual-office-button", VirtualOfficeButton, {
      extends: "button",
    });
  }

  constructor() {
    super();
    this.projectName = this.getAttribute("project-name");
    this.addEventListener("click", () => {
      if (this.connectionUrl) {
        window.open(this.connectionUrl, "_blank");
      } else {
        this.disabled = true;
        deployVM(this.projectName)
          .then(() => {
            displayMessage(
              window.gettext(
                "The virtual office is being created. This may take some time."
              ),
              "success"
            );
            this.waitForDeploymentComplete();
          })
          .catch(() => {
            this.disabled = false;
            displayMessage(
              window.gettext(
                "An error occured while creating the virtual office. Please contact an administrator or try again later."
              ),
              "error"
            );
          });
      }
    });
  }

  connectedCallback() {
    this.disabled = true;
    this.initButton();
  }

  async initButton() {
    const url = await fetchVMConnectionLink(this.projectName);
    if (url) {
      this.connectionUrl = url;
      this.disabled = false;
    } else {
      const deploymentStatus = await fetchDeploymentStatus(this.projectName);
      if (deploymentStatus) {
        this.deploymentStatus = deploymentStatus;
        if (deploymentStatus === "Failed") {
          this.onFailedDeployment();
        } else {
          this.waitForDeploymentComplete();
        }
      } else {
        this.disabled = false;
      }
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

  async checkDeploymentProgress() {
    if (this.deploymentStatus && this.deploymentStatus === "Succeeded") {
      const url = await fetchVMConnectionLink(this.projectName);
      if (url) {
        this.connectionUrl = url;
        this.innerText = window.gettext("Access virtual office");
        this.disabled = false;
        clearInterval(this.checkDeploymentIntervalId);
      }
    } else {
      const deploymentStatus = await fetchDeploymentStatus(this.projectName);
      if (deploymentStatus) {
        this.deploymentStatus = deploymentStatus;
        if (this.deploymentStatus === "Failed") {
          this.onFailedDeployment();
          clearInterval(this.checkDeploymentIntervalId);
        }
      }
    }
  }

  onFailedDeployment() {
    this.innerText = window.gettext("Access virtual office");
    displayMessage(
      window.gettext(
        "We could not create the virtual office. Please contact an administrator."
      ),
      "error"
    );
  }
}
