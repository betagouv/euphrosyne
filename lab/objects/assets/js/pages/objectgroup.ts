import "@gouvfr/dsfr/dist/component/accordion/accordion.module.min.js";

import {
  handleAccordionClick,
  updateObjectRows,
  displaySingleObjectForm,
  displayObjectGroupForm,
  toggleInlineInputsDisabledOnParentChange,
} from "../object/form.js";

document.addEventListener("DOMContentLoaded", function () {
  const getObjectCountInput = () =>
    document.getElementById("id_object_count") as HTMLInputElement;

  const getAreObjectsDifferentiated = () =>
    document
      .querySelector('button[aria-controls="differentiation-accordion"]')
      ?.getAttribute("aria-expanded") === "true";

  function onFormsetChange() {
    const objectCountInput = getObjectCountInput();
    if (!getAreObjectsDifferentiated() && objectCountInput) {
      objectCountInput.value = document
        .querySelectorAll("#object_set-group tbody tr.dynamic-object_set")
        .length.toString();
    }
  }

  document
    .getElementById("objectgroup_form")
    ?.addEventListener("submit", function () {
      // Disabled object inline formset if objects are not differentiated
      const totalFormsInput = document.getElementById(
        "id_object_set-TOTAL_FORMS",
      ) as HTMLInputElement | null;
      if (!getAreObjectsDifferentiated() && totalFormsInput) {
        totalFormsInput.value = "0";
      }
    });

  document
    .getElementById("id_add_type")
    ?.addEventListener("change", function (event) {
      const { value } = event.target as HTMLSelectElement;
      if (value === "SINGLE_OBJECT") {
        displaySingleObjectForm();
      } else if (value === "OBJECT_GROUP") {
        displayObjectGroupForm();
      }
    });

  document
    .getElementById("id_object_count")
    ?.addEventListener("input", function (event) {
      const addTypeInput = document.getElementById(
        "id_add_type",
      ) as HTMLInputElement;
      if (addTypeInput.value === "SINGLE_OBJECT") {
        return;
      }
      updateObjectRows((event.target as HTMLInputElement).value);
    });

  document
    .querySelector('button[aria-controls="differentiation-accordion"]')
    ?.addEventListener("click", function (event) {
      const isExpanded = !(
        (event.target as HTMLButtonElement).getAttribute("aria-expanded") ===
        "true"
      );
      handleAccordionClick(isExpanded, getObjectCountInput().value);
    });

  document
    .getElementById("id_inventory")
    ?.addEventListener("change", (event) => {
      toggleInlineInputsDisabledOnParentChange(
        "inventory",
        (event.target as HTMLInputElement).value,
      );
    });
  document
    .getElementById("id_collection")
    ?.addEventListener("change", (event) => {
      toggleInlineInputsDisabledOnParentChange(
        "collection",
        (event.target as HTMLInputElement).value,
      );
    });

  document.addEventListener("formset:added", onFormsetChange);
  document.addEventListener("formset:removed", onFormsetChange);

  if (
    (document.getElementById("id_object_count") as HTMLInputElement | null)
      ?.value === "1"
  ) {
    displaySingleObjectForm();
  } else {
    displayObjectGroupForm();
  }
});
