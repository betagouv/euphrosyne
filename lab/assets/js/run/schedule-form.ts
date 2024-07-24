export function initRunScheduleForm() {
  document.querySelectorAll(".run-schedule-modal").forEach((element) => {
    setEmbargoDateInputInitialValue(element);
    setEmbargoInputDisabled(element);

    getPermanentEmbargoCheckbox(element)?.addEventListener("change", () => {
      setEmbargoInputDisabled(element);
    });
  });
}

function setEmbargoInputDisabled(parentElement: Element) {
  const embargoInput = getEmbargoDateInput(parentElement);
  (embargoInput as HTMLInputElement).disabled =
    getPermanentEmbargoCheckbox(parentElement).checked;
}

function getPermanentEmbargoCheckbox(parentElement: Element) {
  return parentElement.querySelector(
    "#id_permanent_embargo",
  ) as HTMLInputElement;
}

function getEmbargoDateInput(parentElement: Element) {
  return parentElement.querySelector("#id_embargo_date") as HTMLInputElement;
}

function setEmbargoDateInputInitialValue(parentElement: Element) {
  const value = new Date();
  value.setDate(value.getDate() + 365 * 2);
  getEmbargoDateInput(parentElement).value = value.toISOString().split("T")[0];
}
