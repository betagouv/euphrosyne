import React from "react";

import { formatBytes } from "../utils.js";
import FileTableActionCell from "./file-table-action-cell.jsx";

export default function FileTableRow({
  file,
  onDelete,
  onDownload,
  cols = ["name", "lastModified", "size"],
  renderActionsCellFn = null,
}) {
  return (
    <tr>
      {cols.includes("name") && <td className="file-name-cell">{file.name}</td>}
      {cols.includes("lastModified") && (
        <td>
          {file.lastModified !== null && file.lastModified.toLocaleDateString()}
        </td>
      )}
      {cols.includes("size") && <td>{formatBytes(file.size)}</td>}
      {renderActionsCellFn ? (
        renderActionsCellFn({ file })
      ) : (
        <FileTableActionCell file={file} handlers={{ onDownload, onDelete }} />
      )}
    </tr>
  );
}
