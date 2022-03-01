import { toggleSubFieldsWrapper } from "../run/methods.js";

document.addEventListener("DOMContentLoaded", function () {
  const changeListForm = document.forms["changelist-form"],
    getDeleteRunButtons = () =>
      document.querySelectorAll('[aria-controls="delete-run"]'),
    getActionOptions = () => Array.from(changeListForm.action.options),
    getDeleteSelectedOption = () =>
      getActionOptions().filter((opt) => opt.value == "delete_selected")[0],
    getRunSelectInputs = () =>
      Array.from(changeListForm.elements).filter(
        (el) => el.tagName == "INPUT" && el.classList.contains("action-select")
      ),
    getRunSelectInput = (runId) =>
      getRunSelectInputs().filter((el) => el.value == runId)[0];

  document
    .querySelectorAll(
      ".method-field-wrapper > input,.detector-field-wrapper > input"
    )
    .forEach((el) => {
      toggleSubFieldsWrapper(el);
      el.addEventListener("click", () => toggleSubFieldsWrapper(el), false);
    });

  getDeleteRunButtons().forEach((el) => {
    const runid = el.dataset.runid;
    el.addEventListener("click", () => {
      getActionOptions().forEach((el) => (el.selected = false));
      getDeleteSelectedOption().selected = true;
      getRunSelectInputs().forEach((el) => (el.checked = false));
      getRunSelectInput(runid).checked = true;
      changeListForm.submit();
    });
  });
});
