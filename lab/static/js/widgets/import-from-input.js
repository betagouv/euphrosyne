"use strict";

(function () {
  /**
   * Converts a string to camel case.
   *
   * @param {string} str - The input string to be converted.
   * @returns {string} The camel case version of the input string.
   */
  function camelize(str) {
    return str
      .replace(/(?:^\w|[A-Z]|\b\w)/g, function (word, index) {
        return index === 0 ? word.toLowerCase() : word.toUpperCase();
      })
      .replace(/\s+/g, "");
  }

  /**
   * Performs a POST request to fetch data from the specified URL.
   *
   * @param {string} url - The URL to fetch data from.
   * @param {string} queryParam - The query parameter.
   * @returns {Promise<Response>} A promise that resolves to the response of the fetch request.
   */
  function fetchData(url, queryParam) {
    return fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": document.querySelector(
          "input[name='csrfmiddlewaretoken']",
        ).value,
      },
      body: JSON.stringify({
        query: queryParam,
      }),
    });
  }

  /**
   * Clears error messages within the specified element.
   *
   * @param {HTMLElement} element - The element containing the error messages.
   */
  function clearErrorMessages(element) {
    element.querySelectorAll(".fr-error-text").forEach((el) => {
      el.remove();
    });
  }

  /**
   * Displays an error message within the specified input group element.
   *
   * @param {HTMLElement} inputGroupEl - The input group element to display the error message in.
   * @param {string} errorMessage - The error message to be displayed.
   */
  function displayErrorMessage(inputGroupEl, errorMessage) {
    const errorEl = document.createElement("p");
    errorEl.classList.add("fr-error-text");
    errorEl.textContent = errorMessage;
    inputGroupEl.appendChild(errorEl);
  }

  /**
   * Performs a search operation based on the value obtained from the specified importFromInputEl element.
   *
   * @param {HTMLElement} importFromInputEl - The element containing the input for the search operation.
   */
  function doSearch(importFromInputEl) {
    const inputEl = importFromInputEl.querySelector("input");

    // Check if the input value is empty
    if (!inputEl.value) {
      inputEl.setCustomValidity(
        window.gettext("You must enter a valid value for this field."),
      );
      importFromInputEl.closest("form").reportValidity();
      return;
    }
    inputEl.setCustomValidity("");

    const url = importFromInputEl.dataset.fetchUrl;

    // Clear any existing error messages
    clearErrorMessages(importFromInputEl);
    importFromInputEl.querySelector("button").disabled = true;

    // Takes value and make an http post request to the url defined in the
    // data-fetch-url attr of the widget
    fetchData(url, inputEl.value)
      .then(async (response) => {
        // Display an error message if the response status is 404
        if (response.status === 404) {
          displayErrorMessage(
            importFromInputEl,
            window.gettext("No results found."),
          );
          return;
        } else if (!response.ok) {
          throw new Error(`${response.status}: ${await response.text()}`);
        }
        const data = await response.json();
        for (const key in data) {
          const datasetKey =
            "import" + camelize(key)[0].toUpperCase() + camelize(key).slice(1);
          if (datasetKey in importFromInputEl.dataset) {
            // Update the corresponding input field with the fetched data
            document.getElementById(
              importFromInputEl.dataset[datasetKey],
            ).value = data[key];
          }
        }
      })
      .catch((error) => {
        // Display an error message if an error occurs during the fetch request
        console.error(error);
        displayErrorMessage(
          importFromInputEl,
          window.gettext(
            "An error occured while retrieving the object. Please contact AGLAE team if the error persists.",
          ),
        );
      })
      .finally(() => {
        importFromInputEl.querySelector("button").disabled = false;
      });
  }

  // Event listener: DOMContentLoaded
  /**
   * Initializes the import widget on the DOMContentLoaded event.
   */
  document.addEventListener("DOMContentLoaded", function () {
    // Initialize each import widget
    document.querySelectorAll(".import-from-input").forEach((el) => {
      // Add keydown event listener to the input field for triggering search on "Enter" key press
      el.querySelector("input").addEventListener("keydown", function (e) {
        if (e.key === "Enter") {
          e.preventDefault();
          doSearch(e.target.closest(".import-from-input"));
        }
      });
      // Add click event listener to the search button
      el.querySelector("button").addEventListener("click", function (e) {
        doSearch(e.target.closest(".import-from-input"));
      });
    });
  });
})();
