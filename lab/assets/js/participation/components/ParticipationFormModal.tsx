import { useRef } from "react";
import { Participation, ParticipationType } from "../types";
import ParticipationForm from "./ParticipationForm";

interface ParticipationFormModalProps {
  projectId: number;
  modalId: string;
  modalTitle?: string;
  participationType: ParticipationType;
  participation?: Participation | null;
  onFormSubmit?: () => void;
}

export default function ParticipationFormModal({
  projectId,
  modalId,
  modalTitle,
  participationType,
  participation,
  onFormSubmit,
}: ParticipationFormModalProps) {
  const t = {
    addTitle: window.gettext("Add member to the project"),
    editTitle: window.gettext("Edit project member"),
    close: window.gettext("Close"),
  };

  const title = modalTitle
    ? modalTitle
    : participation
      ? t.editTitle
      : t.addTitle;

  const closeButtonRef = useRef<HTMLButtonElement>(null);

  const closeModal = () => {
    closeButtonRef.current?.click();
  };

  return (
    <dialog
      id={modalId}
      className="fr-modal"
      aria-labelledby={`${modalId}-title`}
      data-fr-concealing-backdrop="true"
    >
      <div className="fr-container fr-container--fluid fr-container-lg">
        <div className="fr-grid-row fr-grid-row--center">
          <div className="fr-col-12 fr-col-md-8 fr-col-lg-6">
            <div className="fr-modal__body">
              <div className="fr-modal__header">
                <button
                  aria-controls={modalId}
                  title={t.close}
                  type="button"
                  className="fr-btn--close fr-btn"
                  ref={closeButtonRef}
                >
                  {t.close}
                </button>
              </div>
              <div className="fr-modal__content">
                <h2 id={`${modalId}-title`} className="fr-modal__title">
                  <span
                    className="fr-icon-user-line fr-icon--lg"
                    aria-hidden="true"
                  ></span>{" "}
                  {title}
                </h2>
                <ParticipationForm
                  participation={participation}
                  projectId={projectId}
                  participationType={participationType}
                  onSuccess={() => {
                    onFormSubmit?.();
                    closeModal();
                  }}
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </dialog>
  );
}
