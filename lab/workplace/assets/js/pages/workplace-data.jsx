import React, { useState, useMemo } from "react";
import { createRoot } from "react-dom/client";
import Fuse from "fuse.js";
import { RawDataFileService } from "../raw-data/raw-data-file-service";
import { ProcessedDataFileService } from "../processed-data/processed-data-file-service";
import {
  QueryClientProvider,
  QueryClient,
  useQuery,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";
import { displayMessage, formatBytes } from "../../../../assets/js/utils";

const queryClient = new QueryClient();

const FileTableRow = ({ file, onDelete, onDownload }) => {
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
    <tr>
      <td>{file.name}</td>
      <td>{formatBytes(file.size)}</td>
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
    </tr>
  );
};

const DirectoryTableRow = ({ file, onOpen }) => {
  return (
    <tr key={file.name}>
      <td>
        <div>
          <span className="fr-icon-folder-2-fill fr-icon--sm fr-mr-1w" />
          {file.name}
        </div>
      </td>
      <td></td>
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
};

const RawDataTable = ({ service }) => {
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
            <th scope="col">
              <div className="text">{window.gettext("File name")}</div>
            </th>
            <th scope="col">
              <div className="text">{window.gettext("Size")}</div>
            </th>
            <th scope="col"></th>
          </tr>
        </thead>
        <tbody>
          {isLoading && (
            <tr class="loading">
              <td>
                <div>&nbsp;</div>
              </td>
              <td>
                <div>&nbsp;</div>
              </td>
              <td>
                <div>&nbsp;</div>
              </td>
            </tr>
          )}

          {!isLoading &&
            (filteredFiles == null || filteredFiles.length <= 0) && (
              <tr className="no_data">
                <td colSpan={3}>{window.gettext("No file yet")}</td>
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
                  <DirectoryTableRow file={file} onOpen={appendFolder} />
                )}
              </React.Fragment>
            ))}
        </tbody>
      </table>
    </div>
  );
};

const RunTabPanel = ({ run, idx }) => {
  const rawService = new RawDataFileService(window.projectSlug, run.name);
  const processedService = new ProcessedDataFileService(
    window.projectSlug,
    run.name
  );

  return (
    <div
      id={`tabpanel-run-${run.id}-panel`}
      className="fr-tabs__panel"
      role="tabpanel"
      aria-labelledby={`tabpanel-run-${run.id}`}
      tabIndex={idx}
    >
      <div className="fr-grid-now fr-grid-now--gutters">
        <div className="fr-col-12">
          <div className="fr-background-default--grey fr-p-3v">
            <h3>HDF5</h3>
          </div>
        </div>
      </div>
      <div className="fr-grid-row fr-grid-row--gutters">
        <div className="fr-col-12 fr-col-lg-6">
          <div className="fr-background-default--grey fr-p-3v">
            <h3>{window.gettext("Raw data")}</h3>
            <RawDataTable service={rawService} />
          </div>
        </div>
        <div className="fr-col-12 fr-col-lg-6">
          <div className="fr-background-default--grey fr-p-3v">
            <h3>{window.gettext("Processed data")}</h3>
            <RawDataTable service={processedService} />
          </div>
        </div>
      </div>
    </div>
  );
};

const WorkplaceApp = () => {
  return (
    <div className="fr-tabs">
      <ul className="fr-tabs__list" role="tablist">
        {window.runs.map((run, idx) => (
          <li key={`tabpanel-button-${run.id}`} role="presentation">
            <button
              id={`tabpanel-run-${run.id}`}
              className="fr-tabs__tab fr-icon-checkbox-line fr-tabs__tab--icon-left"
              tabIndex={idx}
              role="tab"
              aria-selected={idx === 0 ? "true" : "false"}
              aria-controls={`tabpanel-run-${run.id}-panel`}
            >
              {run.name}
            </button>
          </li>
        ))}
      </ul>
      {window.runs.map((run, idx) => (
        <RunTabPanel key={`run-tab-panel-${run.id}`} run={run} idx={idx} />
      ))}
    </div>
  );
};

const container = document.getElementById("workspace-react");
const root = createRoot(container);
root.render(
  <QueryClientProvider client={queryClient}>
    <WorkplaceApp />
  </QueryClientProvider>
);
