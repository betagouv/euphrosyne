import { useContext } from "react";
import { css } from "@emotion/react";

import { FileContext } from "../../../../assets/js/components/FileContext";

interface DocumentTableActionCellProps {
  canDelete: boolean;
  onDownloadClick: (path: string) => void;
  onDeleteClick: (name: string, path: string) => void;
}

const cellStyle = css({
  width: "10rem",
});

export default function DocumentTableActionCell({
  canDelete,
  onDownloadClick,
  onDeleteClick,
}: DocumentTableActionCellProps) {
  const file = useContext(FileContext);

  return (
    <td css={cellStyle}>
      {file && (
        <ul className="fr-btns-group fr-btns-group--inline fr-btns-group--sm">
          <li>
            <button
              className="download-btn fr-btn fr-icon-download-line fr-btn--secondary"
              onClick={() => onDownloadClick(file.path)}
            >
              {window.gettext("Download file")}
            </button>
          </li>
          {canDelete && (
            <li>
              <button
                className="delete-btn fr-btn fr-icon-delete-line fr-btn--secondary"
                onClick={() => onDeleteClick(file.name, file.path)}
              >
                {window.gettext("Delete file")}
              </button>
            </li>
          )}
        </ul>
      )}
    </td>
  );
}
