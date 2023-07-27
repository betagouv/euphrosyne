import React from "react";

export default function FileTableActionCell({
  file,
  handlers: { onDownload, onDelete },
}) {
  const clickDelete = () => {
    if (
      !window.confirm(
        window.interpolate(window.gettext("Delete the document %s ?"), [
          file.name,
        ])
      )
    ) {
      return;
    }

    onDelete(file);
  };
  return (
    <td>
      <ul className="fr-btns-group fr-btns-group--inline fr-btns-group--sm">
        <li>
          <button
            className="download-btn fr-btn fr-icon-download-line fr-btn--secondary"
            title={window.gettext("Download file")}
            onClick={() => onDownload(file)}
          >
            {window.gettext("Download file")}
          </button>
        </li>

        <li>
          <button
            className="delete-btn fr-btn fr-icon-delete-line fr-btn--secondary"
            title={window.gettext("Delete file")}
            onClick={clickDelete}
          >
            {window.gettext("Delete file")}
          </button>
        </li>
      </ul>
    </td>
  );
}
