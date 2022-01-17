(function () {
  function setCounter(target) {
    target.parentElement.querySelector(".countertextarea-counter").innerHTML =
      interpolate(gettext("Characters left: %s"), [
        target.getAttribute("maxlength") - target.value.length,
      ]);
  }
  document.addEventListener("DOMContentLoaded", function () {
    document
      .querySelectorAll(".countertextarea-wrapper textarea")
      .forEach((textarea) => {
        setCounter(textarea);
        textarea.addEventListener("input", (event) => {
          const target = event.target;
          setCounter(target);
        });
      });
  });
})();
