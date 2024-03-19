function onFormSubmit(event) {
  const labeInput = document.querySelector("input[name='label']"),
    c2rmfIdInput = document.querySelector(".import-from-input input");
  if (!labeInput.value) {
    c2rmfIdInput.setCustomValidity(
      window.gettext("Search for a valid C2RMF ID before submitting the form."),
    );
    event.target.reportValidity();
    event.preventDefault();
    return false;
  }
  c2rmfIdInput.setCustomValidity("");
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
