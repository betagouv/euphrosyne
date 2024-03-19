"use strict";

(function () {
  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".choice-tag").forEach((el) => {
      el.addEventListener("click", (event) => {
        event.target.parentElement
          .querySelectorAll("button.choice-tag")
          .forEach((tag) => {
            tag.setAttribute("aria-pressed", false);
          });
        event.target.setAttribute("aria-pressed", true);
        const input = event.target.parentElement.querySelector(
          "input[type='hidden']",
        );
        input.value = event.target.dataset.value;
        input.dispatchEvent(new Event("change"));
      });
    });
  });
})();
