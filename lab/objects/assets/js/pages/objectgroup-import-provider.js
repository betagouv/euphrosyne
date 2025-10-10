function onFormSubmit(event) {
  const labelInput = document.querySelector("input[name='label']"),
    erosIdInput = document.querySelector(".import-from-input input");
  if (!labelInput.value) {
    erosIdInput.setCustomValidity(
      window.gettext("Search for a valid ID before submitting the form."),
    );
    event.target.reportValidity();
    event.preventDefault();
    return false;
  }
  erosIdInput.setCustomValidity("");
}

document.addEventListener("DOMContentLoaded", function () {
  const submitButton = document.querySelector("form input[type='submit']");
  document.querySelector("form").addEventListener("submit", onFormSubmit);
  document
    .querySelector("form input[name='label']")
    .addEventListener("input", function (event) {
      submitButton.disabled = !event.target.value;
    });
});
