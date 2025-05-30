"use strict";

import euphrosyneToolsService from "../euphrosyne-tools-service.js";
import euphrosyneToolsFetch from "../../../../../shared/js/euphrosyne-tools-client.ts";

export default class VMSizeSelect extends HTMLSelectElement {
  static init() {
    customElements.define("vm-size-select", VMSizeSelect, {
      extends: "select",
    });
  }

  get projectName() {
    return this.getAttribute("project-name");
  }

  connectedCallback() {
    this.disabled = true;
    euphrosyneToolsService
      .fetchProjectVmSize(this.projectName, euphrosyneToolsFetch)
      .then((vmSize) => {
        this.value = vmSize || "";
        this.addEventListener("change", this.onSelectChange);
        this.disabled = false;
      });
  }

  async onSelectChange({ target }) {
    const { value } = target;
    await euphrosyneToolsService.setProjectVmSize(
      this.projectName,
      value,
      euphrosyneToolsFetch,
    );
  }
}
