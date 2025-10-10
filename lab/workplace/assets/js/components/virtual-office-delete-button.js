"use strict";

import euphrosyneToolsService from "../euphrosyne-tools-service.js";
import utils from "../../../../assets/js/utils.js";
import euphrosyneToolsFetch from "../../../../../shared/js/euphrosyne-tools-client.ts";

export default class VirtualOfficeDeleteButton extends HTMLButtonElement {
  static init() {
    customElements.define(
      "virtual-office-delete-button",
      VirtualOfficeDeleteButton,
      {
        extends: "button",
      },
    );
  }

  get projectSlug() {
    return this.getAttribute("project-slug");
  }

  constructor() {
    super();
    this.checkDeletingIntervalId = null;
    this.addEventListener("click", this.onButtonClick);
    window.addEventListener("vm-ready", () => {
      this.disabled = false;
    });
  }

  connectedCallback() {
    this.disabled = true;
  }

  async onButtonClick() {
    if (!window.confirm(window.gettext("Delete virtual office ?"))) {
      return;
    }
    this.disabled = true;
    const promise = euphrosyneToolsService.deleteVM(
      this.projectSlug,
      euphrosyneToolsFetch,
    );
    this.checkDeletingIntervalId = setInterval(
      this.checkDeletingProgress.bind(this),
      5000,
    );
    try {
      await promise;
    } catch (error) {
      this.disabled = false;
      utils.displayMessage(
        window.gettext("An error occurred while deleting the virtual office."),
        "error",
      );
      throw error;
    }
    utils.displayMessage(
      window.gettext("The virtual office has been deleted."),
      "success",
    );
    window.dispatchEvent(new CustomEvent("vm-deleted"));
  }

  async checkDeletingProgress() {
    const vmStatus = await euphrosyneToolsService.fetchVMProvisioningState(
      this.projectSlug,
      euphrosyneToolsFetch,
    );
    if (!vmStatus) {
      utils.displayMessage(
        window.gettext(
          "The virtual machine has been shut down and deleted. Please wait for the Guacamole connection to be deleted.",
        ),
        "info",
      );
      clearInterval(this.checkDeletingIntervalId);
      this.checkDeletingIntervalId = null;
    }
  }
}
