(function () {
  function toggleOtherInput(containerElement) {
    const select = containerElement.querySelector("select");
    const selectedOption = select.querySelector("option:checked");
    const otherInput = containerElement.querySelector("input.other-input");
    if (selectedOption && selectedOption.value && selectedOption.value == "_") {
      otherInput.removeAttribute("disabled");
      otherInput.style.display = "";
    } else {
      otherInput.disabled = true;
      otherInput.style.display = "none";
    }
  }
  document.addEventListener("DOMContentLoaded", function (_) {
    document.querySelectorAll(".other-select").forEach(function (otherSelect) {
      const container = otherSelect.parentElement;
      toggleOtherInput(container);
      otherSelect.addEventListener("change", function () {
        toggleOtherInput(container);
      });
    });
  });
})();
