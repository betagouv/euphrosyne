import { useState } from "react";
import { css } from "@emotion/react";

import { RunObjectGroup } from "../types";

import ObjectGroupMaterialsCell from "./ObjectGroupMaterialsCell";

interface ObjectGroupTableProps {
  runId: string;
  runObjectGroups: RunObjectGroup[];
  onRowDelete?: (runObjectGroupId: string) => void;
}

export default function ObjectGroupTable({
  runId,
  runObjectGroups,
  onRowDelete,
}: ObjectGroupTableProps) {
  const t = {
    "No object in this run yet": window.gettext("No object in this run yet"),
    "Remove from run": window.gettext("Remove from run"),
  };

  const [deleting, setDeleting] = useState(false);

  const breakWordCellStyle = css({
    wordBreak: "break-word",
  });
  const actionCellStyle = css({
    width: "4.5rem",
  });

  const onDeleteClick = async (runObjectGroupId: string) => {
    setDeleting(true);
    try {
      onRowDelete?.(runObjectGroupId);
    } catch (e) {
      setDeleting(false);
    }
    setDeleting(false);
  };

  return (
    <div className="fr-table fr-table--bordered fr-table--layout-fixed">
      <table>
        <colgroup>
          <col />
          <col />
          <col />
          <col css={actionCellStyle} />
        </colgroup>
        <tbody>
          {runObjectGroups.length === 0 && (
            <tr>
              <td colSpan={4}>{t["No object in this run yet"]}</td>
            </tr>
          )}
          {runObjectGroups.map(({ objectGroup, id }) => (
            <tr key={`${objectGroup.label}-${objectGroup.id}-row`}>
              <td>
                {objectGroup.objectCount > 1 && (
                  <>
                    <span
                      className="fr-icon-pantone-line"
                      aria-hidden="true"
                    ></span>
                    <strong>{objectGroup.objectCount} </strong>
                  </>
                )}
                <a
                  href={`/lab/objectgroup/${objectGroup.id}/change/?next=/lab/run/${runId}/change/&run=${runId}`}
                >
                  {objectGroup.label}
                </a>
              </td>
              <td css={breakWordCellStyle}>{objectGroup.dating}</td>
              <td>
                <ObjectGroupMaterialsCell materials={objectGroup.materials} />
              </td>
              <td css={actionCellStyle}>
                <button
                  className="fr-btn fr-icon-close-line delete-btn fr-btn--tertiary-no-outline"
                  title={t["Remove from run"]}
                  type="button"
                  disabled={deleting}
                  onClick={() => onDeleteClick(id)}
                ></button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
