export function tabClickHandler(
  initialFormData,
  newFormData,
  onCloseModal,
  event,
) {
  if (JSON.stringify(newFormData) !== JSON.stringify(initialFormData)) {
    event.preventDefault();
    onCloseModal.dataset.nextUrl = event.target.href;
    dsfr(onCloseModal).modal.disclose();
    return false;
  }
}

export function handleModalClose(modal) {
  dsfr(modal).modal.conceal();
}

export function handleModalConfirm(modal) {
  location.assign(modal.dataset.nextUrl);
}
