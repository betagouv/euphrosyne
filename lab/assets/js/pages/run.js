import { getMethodInputs, toggleSubFieldsWrapper } from "../run/methods.js";
import {
  getDeleteRunButtons,
  handleDelete,
  getCards,
  toggleRunSelection,
  getRunChangeStateActionButton,
  handleSubmitChangeStateAction,
} from "../run/changelist.js";

document.addEventListener("DOMContentLoaded", function () {
  getMethodInputs().forEach((el) => {
    toggleSubFieldsWrapper(el);
    el.addEventListener("click", () => toggleSubFieldsWrapper(el), false);
  });

  getDeleteRunButtons().forEach((el) => {
    const runid = el.dataset.runid;
    el.addEventListener("click", () => handleDelete(runid));
  });

  getCards().forEach((el) => {
    el.addEventListener("click", () => toggleRunSelection(el));
  });

  getRunChangeStateActionButton()?.addEventListener(
    "click",
    handleSubmitChangeStateAction
  );
});
