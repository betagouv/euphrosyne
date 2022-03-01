function getSubFieldsElement(inputElement) {
  return inputElement.parentElement.nextElementSibling;
}

export function toggleSubFieldsWrapper(inputElement) {
  const subFieldsElement = getSubFieldsElement(inputElement);
  if (subFieldsElement !== null) {
    subFieldsElement.style.display = inputElement.checked
      ? "inline-block"
      : "none";
  }
}
