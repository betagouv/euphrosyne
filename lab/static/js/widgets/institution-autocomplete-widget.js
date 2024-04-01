"use strict";

(function () {
  const baseSelector = ".autocomplete-input";

  let fetchTimeoutId = null; // for debouncing when fetching from ROR API

  function onResultClicked(event, { country, name, rorId }) {
    const parentField = event.target.closest(".field-institution");
    parentField.querySelector(".autocomplete-input__name").value = name;
    parentField.querySelector(".autocomplete-input__country").value = country;
    parentField.querySelector(".autocomplete-input__ror_id").value = rorId;

    parentField.querySelector(".typeahead-list").classList.add("hidden");
  }

  function onCountryOrNameInput(event) {
    const institutionField = event.target.closest(".field-institution");

    const idInput = institutionField.querySelector(".autocomplete-input__id");
    if (idInput.value && idInput.value !== "") {
      idInput.value = "";
    }
  }

  function onCountryInput(event) {
    onCountryOrNameInput(event);
  }

  async function onNameInput(event) {
    // On institution name input, fetch institutions from ROR API
    const parentElement = event.target.parentElement;

    onCountryOrNameInput(event);

    if (fetchTimeoutId) {
      clearTimeout(fetchTimeoutId); // debounce
    }

    fetchTimeoutId = setTimeout(async () => {
      const response = await fetch(
        "https://api.ror.org/organizations?query=" +
          encodeURIComponent(event.target.value),
      );

      if (!response.ok) {
        return;
      }

      const results = (await response.json()).items;

      const typeaheadList = parentElement.querySelector(".typeahead-list");

      typeaheadList.classList.remove("hidden");

      typeaheadList.querySelectorAll("button").forEach((o) => o.remove());
      results.forEach((result) => {
        const buttonElement = document.createElement("button");
        buttonElement.textContent = `${result.name}, ${result.country?.country_name}`;
        buttonElement.id = result.id;
        buttonElement.type = "button";
        buttonElement.addEventListener("click", (event) =>
          onResultClicked(event, {
            country: result.country?.country_name,
            name: result.name,
            rorId: result.id,
          }),
        );
        parentElement
          .querySelector(".typeahead-list")
          .appendChild(buttonElement);
      });
    }, 500);
  }

  document.addEventListener("DOMContentLoaded", function () {
    // Add event listeners to institution input elements
    document.querySelectorAll(`${baseSelector}`).forEach((el) => {
      el.querySelector(`${baseSelector}__name`).addEventListener(
        "input",
        onNameInput,
      );
      el.querySelector(`${baseSelector}__country`).addEventListener(
        "input",
        onCountryInput,
      );
    });

    document.addEventListener("click", function (event) {
      // Hide typeahead list when clicking outside
      document.querySelectorAll(".typeahead-list").forEach((el) => {
        const isInside = el.contains(event.target);
        if (!isInside && !el.classList.contains("hidden")) {
          el.classList.add("hidden");
        }
      });
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
            .addEventListener("input", onNameInput);
          lastElement
            .querySelector(`${baseSelector}__country`)
            .addEventListener("input", onCountryInput);
        });
    }, 300);
  });
})();
