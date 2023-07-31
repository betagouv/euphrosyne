import React from "react";

export default function DirectoryTableRow({ file, onOpen, cols }) {
  const onDirClick = (e) => {
    e.preventDefault();
    onOpen(file.name);
  };
  return (
    <tr key={file.name} className="directory-row">
      <td>
        <div>
          <span className="fr-icon-folder-2-fill fr-icon--sm fr-mr-1w" />
          <a
            className="fr-link fr-icon-arrow-right-line fr-link--icon-right"
            href="#"
            onClick={onDirClick}
          >
            {file.name}
          </a>
        </div>
      </td>
      <td colSpan={cols.length}></td>
    </tr>
  );
}
