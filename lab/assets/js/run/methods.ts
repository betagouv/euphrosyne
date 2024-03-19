export function getMethodInputs() {
  return document.querySelectorAll(
    ".method-field-wrapper > input,.detector-field-wrapper > input",
  ) as NodeListOf<HTMLElement>;
}

function getSubFieldsElement(inputElement: HTMLElement) {
  return inputElement?.parentElement?.nextElementSibling as HTMLElement;
}

export function toggleSubFieldsWrapper(inputElement: HTMLElement) {
  const subFieldsElement = getSubFieldsElement(inputElement);
  if (
    subFieldsElement &&
    subFieldsElement.style &&
    inputElement instanceof HTMLInputElement
  ) {
    subFieldsElement.style.display = inputElement.checked
      ? "inline-block"
      : "none";
  }
}
