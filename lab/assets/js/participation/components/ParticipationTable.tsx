import RadiationProtectionCheck from "./RadiationProtectionCheck";
import type { CSSProperties } from "react";
import type { Participation } from "../types";

const textCellStyle: CSSProperties = {
  overflowWrap: "anywhere",
  whiteSpace: "normal",
};

const actionCellStyle: CSSProperties = {
  whiteSpace: "nowrap",
};

const actionCellContentStyle: CSSProperties = {
  alignItems: "center",
  display: "flex",
  gap: "0.25rem",
  justifyContent: "flex-end",
  whiteSpace: "nowrap",
};

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
            <table
              style={{
                minWidth: "64rem",
                tableLayout: "fixed",
                width: "100%",
              }}
            >
              <colgroup>
                <col style={{ width: "12%" }} />
                <col style={{ width: "16%" }} />
                <col style={{ width: "22%" }} />
                <col />
                <col style={{ width: "14rem" }} />
              </colgroup>
              {tableCaption && <caption> {tableCaption} </caption>}
              <thead>
                <tr>
                  <th style={textCellStyle}> {t.firstName} </th>
                  <th style={textCellStyle}> {t.lastName} </th>
                  <th style={textCellStyle}> {t.email} </th>
                  <th style={textCellStyle}> {t.institution} </th>
                  <th style={actionCellStyle}> </th>
                </tr>
              </thead>
              <tbody>
                {participations.map((participation) => (
                  <tr key={participation.id}>
                    <td style={textCellStyle}>
                      {participation.user.firstName || "-"}
                    </td>
                    <td style={textCellStyle}>
                      {participation.user.lastName || "-"}
                    </td>
                    <td style={textCellStyle}>{participation.user.email}</td>
                    <td style={textCellStyle}>
                      {participation.institution?.name || "-"}
                      {participation.institution?.country &&
                        `, ${participation.institution.country}`}
                    </td>
                    <td style={actionCellStyle}>
                      <div style={actionCellContentStyle}>
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
                      </div>
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
