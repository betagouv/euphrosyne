import RadiationProtectionCheck from "./RadiationProtectionCheck";
import type { Participation } from "../types";

interface ParticipationTableProps {
  participations: Participation[];
  tableCaption?: string;
  editModalId?: string;
  canDelete?: boolean;
  canEdit?: boolean;
  onDeleteClick?: (participation: Participation) => void;
  onEditClick?: (participation: Participation) => void;
}
export default function ParticipationTable({
  participations,
  tableCaption,
  editModalId,
  canDelete = false,
  canEdit = false,
  onDeleteClick,
  onEditClick,
}: ParticipationTableProps) {
  const t = {
    deleteButtonLabel: window.gettext("Delete participation"),
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
                      {participation.onPremises && (
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
