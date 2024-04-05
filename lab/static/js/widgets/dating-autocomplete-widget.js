"use strict";

(function () {
  const baseSelector = ".dating-autocomplete-input";

  function onResultClicked(event) {
    const { id, label } = event.detail.result;

    const parentField = event.target.closest(baseSelector);
    parentField.querySelector(`${baseSelector}__label`).value = label;
    parentField.querySelector(`${baseSelector}__theso_joconde_id`).value = id;

    parentField.querySelector(".typeahead-list").classList.add("hidden");
  }

  function onInput(event) {
    const datingField = event.target.closest(baseSelector);

    const idInput = datingField.querySelector(`${baseSelector}__id`);
    if (idInput.value && idInput.value !== "") {
      idInput.value = "";
      datingField.querySelector(`${baseSelector}__theso_joconde_id`).value = "";
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    // Add event listeners to institution input elements
    document.querySelectorAll(`${baseSelector}`).forEach((el) => {
      el.querySelector(`${baseSelector}__label`).addEventListener(
        "input",
        onInput,
      );
      el.querySelector("div[is='period-type-ahead']").addEventListener(
        "result-click",
        onResultClicked,
      );
    });
  });
})();
