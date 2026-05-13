import { useEffect, useRef, useState } from "react";
import type { Participation } from "../types";

interface ParticipationTypeSwitchModalProps {
  modalId: string;
  participation: Participation | null;
  onConfirm: (participation: Participation) => Promise<void>;
  onDismiss: () => void;
}

export default function ParticipationTypeSwitchModal({
  modalId,
  participation,
  onConfirm,
  onDismiss,
}: ParticipationTypeSwitchModalProps) {
  const t = {
    title: window.gettext("Switch participation type"),
    close: window.gettext("Close"),
    cancel: window.gettext("Cancel"),
    confirm: window.gettext("Confirm"),
    onSite: window.gettext("on-site"),
    remote: window.gettext("remote"),
    body: window.gettext("Switch %s to %s participation?"),
    error: window.gettext("The participation type could not be switched."),
  };

  const closeButtonRef = useRef<HTMLButtonElement>(null);
  const [isPending, setIsPending] = useState(false);
  const [hasError, setHasError] = useState(false);

  const participantLabel = participation
    ? [participation.user.firstName, participation.user.lastName]
        .filter(Boolean)
        .join(" ") || participation.user.email
    : "";
  const targetType = participation?.onPremises ? t.remote : t.onSite;

  const closeModal = () => {
    closeButtonRef.current?.click();
  };

  const handleDismiss = () => {
    setHasError(false);
    onDismiss();
  };

  useEffect(() => {
    setHasError(false);
  }, [participation?.id]);

  const handleConfirm = async () => {
    if (!participation) {
      return;
    }
    setIsPending(true);
    setHasError(false);
    try {
      await onConfirm(participation);
      closeModal();
    } catch {
      setHasError(true);
    } finally {
      setIsPending(false);
    }
  };

  return (
    <dialog
      id={modalId}
      className="fr-modal"
      aria-labelledby={`${modalId}-title`}
      data-fr-concealing-backdrop="true"
      onCancel={handleDismiss}
      onClose={handleDismiss}
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
                  onClick={handleDismiss}
                >
                  {t.close}
                </button>
              </div>
              <div className="fr-modal__content">
                <h2 id={`${modalId}-title`} className="fr-modal__title">
                  <span
                    className="fr-icon-arrow-left-right-line fr-icon--lg"
                    aria-hidden="true"
                  ></span>{" "}
                  {t.title}
                </h2>
                {participation && (
                  <p>
                    {window.interpolate(t.body, [participantLabel, targetType])}
                  </p>
                )}
                {hasError && (
                  <p className="fr-error-text" aria-live="polite">
                    {t.error}
                  </p>
                )}
              </div>
              <div className="fr-modal__footer">
                <ul className="fr-btns-group fr-btns-group--inline-md">
                  <li>
                    <button
                      type="button"
                      className="fr-btn fr-btn--secondary"
                      aria-controls={modalId}
                      onClick={closeModal}
                      disabled={isPending}
                    >
                      {t.cancel}
                    </button>
                  </li>
                  <li>
                    <button
                      type="button"
                      className="fr-btn"
                      onClick={handleConfirm}
                      disabled={!participation || isPending}
                    >
                      {t.confirm}
                    </button>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </dialog>
  );
}
