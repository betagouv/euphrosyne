(function () {
  function getSubFieldsElement(inputElement) {
    return inputElement.parentElement.nextElementSibling;
  }
  function toggleSubFieldsWrapper(inputElement) {
    const subFieldsElement = getSubFieldsElement(inputElement);
    if (subFieldsElement !== null) {
      subFieldsElement.style.display = inputElement.checked
        ? "inline-block"
        : "none";
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    document
      .querySelectorAll(
        ".method-field-wrapper > input,.detector-field-wrapper > input"
      )
      .forEach(function (el) {
        toggleSubFieldsWrapper(el);
        el.addEventListener(
          "click",
          function () {
            toggleSubFieldsWrapper(el);
          },
          false
        );
      });
  });
})();
