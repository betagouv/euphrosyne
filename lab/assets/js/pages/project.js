import {
  tabClickHandler,
  handleModalClose,
  handleModalConfirm,
} from "../project/tabs.js";

document.addEventListener("DOMContentLoaded", () => {
  const form = Array.from(document.forms).filter(
    (f) => f.id == "project_form"
  )[0];
  const otherTabsAnchors = document.querySelectorAll(
    "#runs-tab > a,#documents-tab > a"
  );
  const onCloseModal = document.getElementById("fr-modal-prdformclose");

  const initialFormData = Array.from(new FormData(form));

  otherTabsAnchors.forEach((a) => {
    a.addEventListener("click", (e) =>
      tabClickHandler(
        initialFormData,
        Array.from(new FormData(form)),
        onCloseModal,
        e
      )
    );
  });

  onCloseModal
    ?.querySelector('[aria-controls="fr-modal-prdformclose-cancel"]')
    .addEventListener("click", () => handleModalClose(onCloseModal));
  onCloseModal
    ?.querySelector('[aria-controls="fr-modal-prdformclose-confirm"]')
    .addEventListener("click", () => handleModalConfirm(onCloseModal));
});
