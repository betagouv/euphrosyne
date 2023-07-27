import React from "react";

export default function HDF5TableActionCell({ file, handlers: {}, projectId }) {
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
          <a href={`/lab/project/${projectId}/hdf5-viewer?file=${path}`}>
            {window.gettext("View")}
          </a>
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
