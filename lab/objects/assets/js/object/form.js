const getObjectsInlineEl = () => document.getElementById("object_set-group"),
  getObjectRows = () =>
    getObjectsInlineEl().querySelectorAll("tbody tr.dynamic-object_set"),
  getObjectsInlineFieldset = () =>
    document.getElementById("object_set-fieldset"),
  getObjectCountField = () => document.querySelector(".field-object_count"),
  getObjectCountInput = () => document.getElementById("id_object_count"),
  getAccordionButton = () =>
    document.querySelector('button[aria-controls="differentiation-accordion"]');

export function handleAccordionClick(isExpanded, objectCountValue) {
  if (isExpanded) {
    getObjectCountField().style.display = "none";
    updateObjectRows(objectCountValue);
  } else {
    getObjectCountField().style.display = null;
    deleteRows(Array.from(getObjectRows()));
  }
}

export function displaySingleObjectForm() {
  const objectCountInput = getObjectCountInput();
  objectCountInput.setAttribute("min", 1);
  objectCountInput.value = 1;
  getObjectCountField().classList.add("hidden");
  document
    .querySelector("button[data-value='OBJECT_GROUP']")
    .setAttribute("aria-pressed", false);
  document
    .querySelector("button[data-value='SINGLE_OBJECT']")
    .setAttribute("aria-pressed", true);

  updateObjectRows(0);
  getObjectsInlineFieldset().classList.add("hidden");
}

export function displayObjectGroupForm() {
  const objectCountInput = getObjectCountInput();

  if (objectCountInput.value < 2) {
    objectCountInput.value = 2;
  }
  objectCountInput.setAttribute("min", 2);
  objectCountInput.setAttribute("type", "number");
  getObjectCountField().classList.remove("hidden");
  document
    .querySelector("button[data-value='OBJECT_GROUP']")
    .setAttribute("aria-pressed", true);
  document
    .querySelector("button[data-value='SINGLE_OBJECT']")
    .setAttribute("aria-pressed", false);

  getObjectsInlineFieldset().classList.remove("hidden");
  getAccordionButton().setAttribute("aria-expanded", false);
}

export function updateObjectRows(newObjectCount) {
  const objectRows = getObjectRows();
  if (objectRows.length < newObjectCount) {
    for (let i = objectRows.length; i < newObjectCount; i++) {
      getObjectsInlineEl().querySelector("tr.add-row a").click();
    }
  } else if (objectRows.length > newObjectCount) {
    const toDeleteRows = Array.from(objectRows).splice(
      newObjectCount - objectRows.length
    );
    deleteRows(toDeleteRows);
  }
}

export function toggleInlineInputsDisabledOnParentChange(
  fieldName,
  inputValue
) {
  const parentHasValue = inputValue !== "",
    inlineInputs = getObjectsInlineEl().querySelectorAll(
      `.field-${fieldName} input`
    );
  inlineInputs.forEach((el) => (el.disabled = parentHasValue));
}

function deleteRows(rowArray) {
  rowArray.forEach((el) => {
    el.querySelector("a.inline-deletelink").dispatchEvent(new Event("click"));
  });
}
