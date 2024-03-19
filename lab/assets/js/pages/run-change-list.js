import {
  getDeleteRunButtons,
  handleDelete,
  getCards,
  toggleRunSelection,
  getRunChangeStateActionButton,
  handleSubmitChangeStateAction,
} from "../run/changelist.js";

document.addEventListener("DOMContentLoaded", function () {
  getDeleteRunButtons().forEach((el) => {
    const runid = el.dataset.runid;
    el.addEventListener("click", (e) => {
      handleDelete(runid);
      // Stop the propagation to avoid triggering the card selection event
      e.stopPropagation();
    });
  });

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
