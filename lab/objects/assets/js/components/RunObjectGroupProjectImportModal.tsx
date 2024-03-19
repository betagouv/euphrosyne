import { ObjectGroup } from "../types";

interface RunObjectGroupProjectImportModalProps {
  id: string;
  availableObjectGroups: ObjectGroup[];
  error?: string | null;
  onAdd: (objectGroupId: string) => void;
}

const objectGroupToOptionLabel = (objectGroup: ObjectGroup) => {
  let label = objectGroup.label;
  if (objectGroup.objectCount > 1) {
    label = `(${objectGroup.objectCount}) ${label}`;
  }
  if (objectGroup.dating) {
    label = `${label} [${objectGroup.dating}]`;
  }
  return label;
};

export default function RunObjectGroupProjectImportModal({
  id,
  availableObjectGroups,
  error,
  onAdd,
}: RunObjectGroupProjectImportModalProps) {
  const t = {
    Close: window.gettext("Close"),
    "Import an object group or object from project": window.gettext(
      "Import an object group or object from project"
    ),
    "Select an existing object group": window.gettext(
      "Select an existing object group"
    ),
    "%s objects are available for import.": window.gettext(
      "%s objects are available for import."
    ),
    "Select an object": window.gettext("Select an object"),
    "Add object to run": window.gettext("Add object to run"),
  };

  let selectedValue = "";
  return (
    <dialog
      aria-labelledby={`${id}-btn`}
      id={id}
      className="fr-modal"
      role="dialog"
    >
      <div className="fr-container fr-container--fluid fr-container-md">
        <div className="fr-grid-row fr-grid-row--center">
          <div className="fr-col-12 fr-col-md-8 fr-col-lg-6">
            <div className="fr-modal__body">
              <div className="fr-modal__header">
                <button
                  className="fr-btn--close fr-btn"
                  aria-controls={id}
                  type="button"
                >
                  {t["Close"]}
                </button>
              </div>
              <div className="fr-modal__content">
                <h1 className="fr-modal__title">
                  {t["Import an object group or object from project"]}
                </h1>
                <div
                  className={`fr-select-group ${
                    error ? "fr-select-group--error" : ""
                  } ${
                    availableObjectGroups.length === 0
                      ? "fr-select-group--disabled"
                      : ""
                  }`}
                >
                  <label className="fr-label" htmlFor={`${id}-select`}>
                    {t["Select an existing object group"]}
                    <span className="fr-hint-text">
                      {window.interpolate(
                        t["%s objects are available for import."],
                        [availableObjectGroups.length.toString()]
                      )}
                    </span>
                  </label>
                  <select
                    className="fr-select"
                    id={`${id}-select`}
                    name="select"
                    defaultValue=""
                    aria-describedby={`${id}-select-error-desc-error`}
                    disabled={availableObjectGroups.length === 0}
                    onChange={(e) => {
                      selectedValue = e.target.value;
                    }}
                  >
                    <option value="" disabled hidden>
                      {t["Select an object"]}
                    </option>
                    {availableObjectGroups.map((og) => (
                      <option key={og.id} value={og.id}>
                        {objectGroupToOptionLabel(og)}
                      </option>
                    ))}
                  </select>
                  {error && (
                    <p
                      id={`${id}-select-error-desc-error`}
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
                    className="fr-btn fr-icon-add-circle-line fr-btn--icon-left"
                    type="button"
                    onClick={() => onAdd(selectedValue)}
                  >
                    {t["Add object to run"]}
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
