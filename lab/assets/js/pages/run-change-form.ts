import { createElement } from "react";

import { getMethodInputs, toggleSubFieldsWrapper } from "../run/methods";
import { renderComponent } from "../../../../euphrosyne/assets/js/react";
import { getTemplateJSONData } from "../../../../shared/js/utils";

import RunObjectGroupForm from "../../../objects/assets/js/components/RunObjectGroupForm";

interface RunChangeFormData {
  run: {
    id: string;
    label: string;
  };
}

document.addEventListener("DOMContentLoaded", async function () {
  const popupObjectGroupEventTarget = new EventTarget();

  window.dismissAddRelatedObjectGroupPopup = (win: Window) => {
    popupObjectGroupEventTarget.dispatchEvent(new Event("objectGroupAdded"));
    win.close();
  };

  getMethodInputs().forEach((el) => {
    toggleSubFieldsWrapper(el);
    el.addEventListener("click", () => toggleSubFieldsWrapper(el), false);
  });

  const runChangeFormData = getTemplateJSONData<RunChangeFormData>(
    "run-change-form-data",
  );
  if (!runChangeFormData) {
    throw new Error("Run ID not found in run-change-form-data script tag.");
  }
  const { run } = runChangeFormData;
  renderComponent(
    "run-objectgroup-form",
    createElement(RunObjectGroupForm, {
      run,
      popupObjectGroupEventTarget,
    }),
  );
});
