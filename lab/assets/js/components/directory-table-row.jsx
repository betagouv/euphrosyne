import React from "react";

export default function DirectoryTableRow({ file, onOpen, cols }) {
  return (
    <tr key={file.name}>
      <td>
        <div>
          <span className="fr-icon-folder-2-fill fr-icon--sm fr-mr-1w" />
          {file.name}
        </div>
      </td>
      <td colSpan={cols.length - 1}></td>
      <td>
        <ul className="fr-btns-group fr-btns-group--inline fr-btns-group--sm">
          <li>
            <button
              className="fr-btn fr-icon-arrow-right-line fr-btn--secondary"
              onClick={() => onOpen(file.name)}
            >
              Open
            </button>
          </li>
        </ul>
      </td>
    </tr>
  );
}
