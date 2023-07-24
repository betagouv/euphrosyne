import React, { useState, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Fuse from "fuse.js";

import DirectoryTableRow from "./directory-table-row.jsx";
import FileTableRow from "./file-table-row.jsx";
import { displayMessage } from "../utils.js";

export default function FileTable({
  service,
  cols = ["name", "lastModified", "size"],
}) {
  const [folder, setFolder] = useState([]);
  const [query, setQuery] = useState("");
  const queryClient = useQueryClient();
  const { isLoading, data: files } = useQuery(
    ["fetch-raw-data", service.listFileURL, folder],
    async () => {
      const files = await service.listData(folder.join("/"));
      return files;
    },
    { refetchOnMount: false, refetchOnReconnect: false }
  );

  const { mutate: deleteFile } = useMutation(
    (file) => service.deleteFile(file.path),
    {
      onSuccess: (_data, variable) => {
        queryClient.invalidateQueries(["fetch-raw-data", service.listFileURL]);
        displayMessage(
          window.interpolate(window.gettext("File %s has been removed."), [
            variable.name,
          ]),
          "success"
        );
      },
      onError: (_error, variable) => {
        displayMessage(
          window.interpolate(window.gettext("File %s could not be removed."), [
            variable.name,
          ]),
          "error"
        );
      },
    }
  );

  const fuse = useMemo(() => {
    return new Fuse(files, {
      includeScore: true,
      keys: ["name"],
    });
  }, [files]);

  const filteredFiles = useMemo(() => {
    if (query === "") {
      return files;
    }

    return fuse.search(query).map((i) => i.item);
  }, [fuse, query]);

  const appendFolder = (name) => {
    setFolder((prev) => [...prev, name]);
  };

  const removeLastFolder = () => {
    setFolder((prev) => prev.slice(0, -1));
  };

  const onDownloadFile = async (file) => {
    const url = await service.fetchPresignedURL(file.path);
    window.open(url, "_blank");
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
      <input
        className="fr-input fr-mb-1w"
        name="query"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder={window.gettext("Search files")}
      />

      <table is="file-table" cols="name,size">
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
          {isLoading && (
            <tr className="loading">
              {Array.from(Array(cols.length + 1)).map((_, idx) => (
                <td key={idx}>
                  <div>&nbsp;</div>
                </td>
              ))}
            </tr>
          )}

          {!isLoading &&
            (filteredFiles == null || filteredFiles.length <= 0) && (
              <tr className="no_data">
                <td colSpan={cols.length}>{window.gettext("No file yet")}</td>
              </tr>
            )}

          {!isLoading &&
            filteredFiles != null &&
            filteredFiles.map((file) => (
              <React.Fragment key={file.name}>
                {file.type === "file" && (
                  <FileTableRow
                    file={file}
                    onDelete={deleteFile}
                    onDownload={onDownloadFile}
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
