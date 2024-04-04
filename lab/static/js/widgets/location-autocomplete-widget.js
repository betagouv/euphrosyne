"use strict";

(function () {
  const baseSelector = ".location-autocomplete-input";

  function onResultClicked(event) {
    const {
      id,
      label,
      attrs: { latitude, longitude },
    } = event.detail.result;

    const parentField = event.target.closest(baseSelector);
    parentField.querySelector(".location-autocomplete-input__label").value =
      label;
    parentField.querySelector(
      ".location-autocomplete-input__geonames_id",
    ).value = id;
    parentField.querySelector(".location-autocomplete-input__latitude").value =
      latitude;
    parentField.querySelector(".location-autocomplete-input__longitude").value =
      longitude;

    parentField.querySelector(".typeahead-list").classList.add("hidden");
  }

  function onLocationInput(event) {
    const institutionField = event.target.closest(baseSelector);

    const idInput = institutionField.querySelector(`${baseSelector}__id`);
    if (idInput.value && idInput.value !== "") {
      idInput.value = "";
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    // Add event listeners to institution input elements
    document.querySelectorAll(`${baseSelector}`).forEach((el) => {
      el.querySelector(`${baseSelector}__label`).addEventListener(
        "input",
        onLocationInput,
      );
      el.querySelector("div[is='location-type-ahead']").addEventListener(
        "result-click",
        onResultClicked,
      );
    });
  });
})();
