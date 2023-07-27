import React from "react";

import DirectoryTableRow from "./directory-table-row.jsx";
import FileTableRow from "./file-table-row.jsx";

export default function FileTable({
  files,
  loading,
  onFileSearch,
  onFileDelete,
  onFileDownload,
  folder,
  setFolder,
  searchQuery,
  cols = ["name", "lastModified", "size"],
  renderActionsCellFn = null,
}) {
  const appendFolder = (name) => {
    setFolder((prev) => [...prev, name]);
  };

  const removeLastFolder = () => {
    setFolder((prev) => prev.slice(0, -1));
  };

  return (
    <div>
      {folder.length > 0 && (
        <div
          style={{
            display: "flex",
            justifyItems: "center",
            alignItems: "center",
          }}
          className="fr-mb-1w"
        >
          <button
            className="fr-btn fr-icon-arrow-left-line fr-btn--sm fr-btn--secondary fr-mr-1w"
            onClick={removeLastFolder}
          />
          <div>/{folder.join("/")}</div>
        </div>
      )}

      <div className="fr-search-bar fr-mb-1w" role="search">
        <label className="fr-label" htmlFor="file-search">
          Recherche
        </label>
        <input
          className="fr-input"
          placeholder={window.gettext("Search files")}
          type="search"
          id="file-search"
          value={searchQuery}
          onChange={onFileSearch}
          name="query"
        />
      </div>

      <table class="file-table" is="file-table" cols="name,size">
        <thead>
          <tr>
            {cols.includes("name") && (
              <th scope="col">
                <div className="text">{window.gettext("File name")}</div>
              </th>
            )}
            {cols.includes("lastModified") && (
              <th scope="col">
                <div className="text">{window.gettext("Last modified")}</div>
              </th>
            )}
            {cols.includes("size") && (
              <th scope="col">
                <div className="text">{window.gettext("Size")}</div>
              </th>
            )}
            <th scope="col"></th>
          </tr>
        </thead>
        <tbody>
          {loading && (
            <tr className="loading">
              {Array.from(Array(cols.length + 1)).map((_, idx) => (
                <td key={idx}>
                  <div>&nbsp;</div>
                </td>
              ))}
            </tr>
          )}

          {!loading && (files == null || files.length <= 0) && (
            <tr className="no_data">
              <td colSpan={cols.length}>{window.gettext("No file yet")}</td>
            </tr>
          )}

          {!loading &&
            files != null &&
            files.map((file) => (
              <React.Fragment key={file.name}>
                {file.type === "file" && (
                  <FileTableRow
                    file={file}
                    onDelete={onFileDelete}
                    onDownload={onFileDownload}
                    renderActionsCellFn={renderActionsCellFn}
                  />
                )}
                {file.type === "directory" && (
                  <DirectoryTableRow
                    file={file}
                    onOpen={appendFolder}
                    cols={cols}
                  />
                )}
              </React.Fragment>
            ))}
        </tbody>
      </table>
    </div>
  );
}
