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
    try {
      await euphrosyneToolsService.deleteVM(
        this.projectSlug,
        euphrosyneToolsFetch,
      );
    } catch (error) {
      this.disabled = false;
      utils.displayMessage(
        window.gettext("An error occured while deleting the virtual office."),
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
}
