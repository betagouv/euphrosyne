"use strict";

(function () {
  const baseSelector = ".autocomplete-input";

  function onNameInput(event) {
    const parentElement = event.target.parentElement;
    const options = parentElement.querySelectorAll("datalist option");
    const index = Array.from(options).findIndex(
      (o) => o.value === event.target.value
    );
    if (index === -1) {
      parentElement.querySelector(`${baseSelector}__id`).value = "";
    } else {
      const [name, country] = event.target.value.split(", ");
      if (country) {
        parentElement.querySelector(`${baseSelector}__country`).value = country;
      }
      parentElement.querySelector(`${baseSelector}__name`).value = name;
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(`${baseSelector}`).forEach((el) => {
      el.querySelector(`${baseSelector}__name`).addEventListener(
        "input",
        onNameInput
      );
    });

    setTimeout(() => {
      document
        .querySelector("#participation_set-group .add-row a")
        .addEventListener("click", function () {
          console.log("clicked");
          const elements = document.querySelectorAll(
            ".dynamic-participation_set"
          );
          const lastElement = elements[elements.length - 1];
          console.log(lastElement);
          lastElement
            .querySelector(`${baseSelector}__name`)
            .addEventListener("input", onNameInput);
        });
    }, 300);
  });
})();
