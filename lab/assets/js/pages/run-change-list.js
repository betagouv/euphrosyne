import {
  getCards,
  toggleRunSelection,
  getRunChangeStateActionButton,
  handleSubmitChangeStateAction,
} from "../run/changelist.js";

document.addEventListener("DOMContentLoaded", function () {
  getCards().forEach((el) => {
    el.addEventListener("click", () => toggleRunSelection(el));

    // Stop the propagation to avoid triggering the card selection event
    el.querySelectorAll("a").forEach((linkEl) => {
      linkEl.addEventListener("click", (e) => {
        e.stopPropagation();
      });
    });
  });

  getRunChangeStateActionButton()?.addEventListener(
    "click",
    handleSubmitChangeStateAction,
  );
});
