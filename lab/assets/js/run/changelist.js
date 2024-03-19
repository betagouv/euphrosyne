const getChangeListForm = () => document.forms["changelist-form"];
export const getDeleteRunButtons = () =>
  document.querySelectorAll('[aria-controls="delete-run"]');
const getActionOptions = () => Array.from(getChangeListForm().action.options);
const getDeleteSelectedOption = () =>
  getActionOptions().filter((opt) => opt.value == "delete_selected")[0];
const getRunSelectInputs = () =>
  Array.from(getChangeListForm().elements).filter(
    (el) => el.tagName == "INPUT" && el.classList.contains("action-select"),
  );
const getRunSelectInput = (runId) =>
  getRunSelectInputs().filter((el) => el.value == runId)[0];

export const handleDelete = (runid) => {
  getActionOptions().forEach((el) => (el.selected = false));
  getDeleteSelectedOption().selected = true;
  getRunSelectInputs().forEach((el) => (el.checked = false));
  getRunSelectInput(runid).checked = true;
  getChangeListForm().submit();
};

export const getCards = () => document.querySelectorAll(".run-clickable-card");
export const getRunChangeStateActionButton = () =>
  document.getElementById("run-changestate-action");

export const toggleRunSelection = (card) => {
  const runid = card.dataset.runid;

  getCards().forEach((el) => {
    el.classList.remove("run-clickable-card__selected");
  });
  getRunSelectInputs().forEach((el) => (el.checked = false));
  card.classList.add("run-clickable-card__selected");
  getRunSelectInput(runid).checked = true;

  if (card.dataset.changestateaction) {
    getRunChangeStateActionButton().style.display = null;
    getRunChangeStateActionButton().innerText = card.dataset.changestateaction;
  } else {
    getRunChangeStateActionButton().style.display = "none";
    getRunChangeStateActionButton().innerText = "";
  }
};

const getChangeStateSelectedOption = () =>
  getActionOptions().filter((opt) => opt.value == "change_state")[0];

export const handleSubmitChangeStateAction = () => {
  getActionOptions().forEach((el) => (el.selected = false));
  getChangeStateSelectedOption().selected = true;
  return true;
};
