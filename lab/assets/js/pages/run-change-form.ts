import { getMethodInputs, toggleSubFieldsWrapper } from "../run/methods";

document.addEventListener("DOMContentLoaded", function () {
  getMethodInputs().forEach((el) => {
    toggleSubFieldsWrapper(el);
    el.addEventListener("click", () => toggleSubFieldsWrapper(el), false);
  });
});
