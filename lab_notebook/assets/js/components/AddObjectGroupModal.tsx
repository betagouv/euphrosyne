import { useRef, useState } from "react";
import {
  createObjectGroup,
  addObjectGroupToRun,
} from "../../../../lab/objects/assets/js/services";
import { updateMeasuringPointObjectId } from "../../../../lab/assets/js/measuring-point.services";

export default function AddObjectGroupModal({
  runId,
  measuringPointId,
  runObjectGroupLabels,
  onAddSuccess,
}: {
  runId: string;
  measuringPointId: string | null;
  runObjectGroupLabels: string[];
  onAddSuccess?: () => void;
}) {
  const t = {
    close: window.gettext("Close"),
    addObjectGroup: window.gettext("Add a new object group / object"),
    name: window.gettext("Object name / reference"),
    save: window.gettext("Save"),
    createObjectError: window.gettext(
      "An error occurred while creating the object group / object.",
    ),
    addObjectErrorToRun: window.gettext(
      "An error occurred while adding the object group / object to the run.",
    ),
    objectGroupAlreadyExistError: window.gettext(
      "An object group / object with this label already exists in this run.",
    ),
    addObjectErrorToPoint: window.gettext(
      "An error occurred while adding the object group / object to the measuring point.",
    ),
  };

  const [objectGroupLabel, setObjectGroupLabel] = useState<string>("");
  const [error, setError] = useState<string>("");

  const closeButtonRef = useRef<HTMLButtonElement>(null);

  const onSaveClicked = async () => {
    let objectGroup;
    if (objectGroupLabel === "" || !measuringPointId) {
      return;
    }
    if (runObjectGroupLabels.includes(objectGroupLabel)) {
      setError(t.objectGroupAlreadyExistError);
    }
    try {
      objectGroup = await createObjectGroup({
        label: objectGroupLabel,
      });
    } catch {
      setError(t.createObjectError);
      return;
    }
    try {
      await addObjectGroupToRun(runId, objectGroup.id.toString());
    } catch {
      setError(t.addObjectErrorToRun);
      return;
    }
    try {
      await updateMeasuringPointObjectId(
        runId,
        measuringPointId,
        objectGroup.id.toString(),
      );
    } catch {
      setError(t.addObjectErrorToPoint);
      return;
    }
    setObjectGroupLabel("");
    if (onAddSuccess) {
      closeButtonRef.current?.click();
      onAddSuccess();
    }
  };

  const onInput = (event: React.FormEvent<HTMLInputElement>) => {
    setObjectGroupLabel((event.target as HTMLInputElement).value);
  };

  const modalId = "add-object-group-modal";

  return (
    <dialog
      aria-labelledby={`${modalId}-title`}
      role="dialog"
      id={modalId}
      className="fr-modal"
    >
      <div className="fr-container fr-container--fluid fr-container-md">
        <div className="fr-grid-row fr-grid-row--center">
          <div className="fr-col-12 fr-col-md-6">
            <div className="fr-modal__body">
              <div className="fr-modal__header">
                <button
                  className="fr-btn--close fr-btn"
                  title={t.close}
                  aria-controls={modalId}
                  ref={closeButtonRef}
                >
                  {t.close}
                </button>
              </div>
              <div className="fr-modal__content">
                <h1 id={`${modalId}-title`} className="fr-modal__title">
                  {t.addObjectGroup}
                </h1>
                <div className="fr-input-group">
                  <label className="fr-label" htmlFor="objectgroup-name-input">
                    {t.name}
                  </label>
                  <input
                    className={`fr-input ${error ? "fr-input-group--error" : ""}`}
                    type="text"
                    id="objectgroup-name-input"
                    aria-describedby="objectgroup-name-input-error"
                    onInput={onInput}
                  />
                  {error && (
                    <p
                      id="objectgroup-name-input-error"
                      className="fr-error-text"
                    >
                      {error}
                    </p>
                  )}
                </div>
              </div>
              <div className="fr-modal__footer">
                <div className="fr-btns-group fr-btns-group--right fr-btns-group--inline-reverse fr-btns-group--inline-lg fr-btns-group--icon-left">
                  <button
                    className="fr-btn"
                    onClick={onSaveClicked}
                    disabled={!measuringPointId || !objectGroupLabel}
                  >
                    {t.save}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </dialog>
  );
}
