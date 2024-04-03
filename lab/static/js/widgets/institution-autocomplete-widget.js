"use strict";

(function () {
  const baseSelector = ".autocomplete-input";

  function onResultClicked(event) {
    const {
      id,
      attrs: { country, name },
    } = event.detail.result;

    const parentField = event.target.closest(".field-institution");
    parentField.querySelector(".autocomplete-input__name").value = name;
    parentField.querySelector(".autocomplete-input__country").value = country;
    parentField.querySelector(".autocomplete-input__ror_id").value = id;

    parentField.querySelector(".typeahead-list").classList.add("hidden");
  }

  function onCountryOrNameInput(event) {
    const institutionField = event.target.closest(".field-institution");

    const idInput = institutionField.querySelector(".autocomplete-input__id");
    if (idInput.value && idInput.value !== "") {
      idInput.value = "";
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    // Add event listeners to institution input elements
    document.querySelectorAll(`${baseSelector}`).forEach((el) => {
      el.querySelector(`${baseSelector}__name`).addEventListener(
        "input",
        onCountryOrNameInput,
      );
      el.querySelector(`${baseSelector}__country`).addEventListener(
        "input",
        onCountryOrNameInput,
      );
      el.querySelector("div[is='institution-type-ahead']").addEventListener(
        "result-click",
        onResultClicked,
      );
    });

    setTimeout(() => {
      // Add event listeners to new institution input elements
      document
        .querySelector("#participation_set-group .add-row a")
        .addEventListener("click", function () {
          const elements = document.querySelectorAll(
            ".dynamic-participation_set",
          );
          const lastElement = elements[elements.length - 1];
          lastElement
            .querySelector(`${baseSelector}__name`)
            .addEventListener("input", onCountryOrNameInput);
          lastElement
            .querySelector(`${baseSelector}__country`)
            .addEventListener("input", onCountryOrNameInput);
          lastElement
            .querySelector("div[is='institution-type-ahead']")
            .setAttribute(
              "html-for",
              lastElement.querySelector(`${baseSelector}__name`).id,
            );
          lastElement
            .querySelector("div[is='institution-type-ahead']")
            .addEventListener("result-click", onResultClicked);
        });
    }, 300);
  });
})();
