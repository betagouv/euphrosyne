import RadiationProtectionCheck from "./RadiationProtectionCheck";
import type { Participation } from "../types";

interface ParticipationTableProps {
  participations: Participation[];
  tableCaption?: string;
  editModalId?: string;
  switchTypeModalId?: string;
  canDelete?: boolean;
  canEdit?: boolean;
  canSwitchType?: boolean;
  onDeleteClick?: (participation: Participation) => void;
  onEditClick?: (participation: Participation) => void;
  onSwitchTypeClick?: (participation: Participation) => void;
  isRadiationProtectionEnabled?: boolean;
}
export default function ParticipationTable({
  participations,
  tableCaption,
  editModalId,
  switchTypeModalId,
  canDelete = false,
  canEdit = false,
  canSwitchType = false,
  onDeleteClick,
  onEditClick,
  onSwitchTypeClick,
  isRadiationProtectionEnabled,
}: ParticipationTableProps) {
  const t = {
    deleteButtonLabel: window.gettext("Delete participation"),
    switchToRemoteButtonLabel: window.gettext("Switch to remote participation"),
    switchToOnSiteButtonLabel: window.gettext(
      "Switch to on-site participation",
    ),
    firstName: window.gettext("First name"),
    lastName: window.gettext("Last name"),
    email: window.gettext("Email"),
    institution: window.gettext("Institution"),
  };

  const _onEditClick = (participation: Participation) => {
    if (editModalId) {
      // @ts-expect-error: Property 'dsfr' does not exist on type 'Window & typeof globalThis'.ts(2339)
      window.dsfr(document.getElementById(editModalId)).modal.disclose();
    }
    onEditClick?.(participation);
  };

  const _onSwitchTypeClick = (participation: Participation) => {
    onSwitchTypeClick?.(participation);
  };

  return (
    <div className="fr-table fr-table--lg">
      <div className="fr-table__wrapper">
        <div className="fr-table__container">
          <div className="fr-table__content">
            <table>
              {tableCaption && <caption> {tableCaption} </caption>}
              <thead>
                <tr>
                  <th> {t.firstName} </th>
                  <th> {t.lastName} </th>
                  <th> {t.email} </th>
                  <th> {t.institution} </th>
                  <th> </th>
                </tr>
              </thead>
              <tbody>
                {participations.map((participation) => (
                  <tr key={participation.id}>
                    <td>{participation.user.firstName || "-"}</td>
                    <td>{participation.user.lastName || "-"}</td>
                    <td>{participation.user.email}</td>
                    <td>
                      {participation.institution?.name || "-"}{" "}
                      {participation.institution?.country &&
                        `, ${participation.institution.country}`}
                    </td>
                    <td>
                      {canEdit && (
                        <button
                          type="button"
                          className="fr-btn fr-icon-edit-box-line fr-btn--tertiary-no-outline"
                          aria-controls={editModalId}
                          onClick={() => _onEditClick(participation)}
                        ></button>
                      )}
                      {canSwitchType && (
                        <>
                          <button
                            type="button"
                            className="fr-btn fr-icon-arrow-left-right-line fr-btn--tertiary-no-outline"
                            aria-controls={switchTypeModalId}
                            aria-describedby={`participation-type-switch-${participation.id}-tooltip`}
                            aria-label={
                              participation.onPremises
                                ? t.switchToRemoteButtonLabel
                                : t.switchToOnSiteButtonLabel
                            }
                            onClick={() => _onSwitchTypeClick(participation)}
                          ></button>
                          <span
                            className="fr-tooltip fr-placement"
                            id={`participation-type-switch-${participation.id}-tooltip`}
                            role="tooltip"
                            aria-hidden="true"
                          >
                            {participation.onPremises
                              ? t.switchToRemoteButtonLabel
                              : t.switchToOnSiteButtonLabel}
                          </span>
                        </>
                      )}
                      {canDelete && (
                        <button
                          type="button"
                          className="fr-btn fr-icon-close-line fr-btn--tertiary-no-outline"
                          onClick={() =>
                            onDeleteClick && onDeleteClick(participation)
                          }
                        >
                          {t.deleteButtonLabel}
                        </button>
                      )}
                      {participation.onPremises &&
                        isRadiationProtectionEnabled && (
                          <span
                            className="fr-p-2v"
                            style={{ display: "inline-block" }}
                          >
                            <RadiationProtectionCheck
                              userId={participation.user.id}
                            />
                          </span>
                        )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
