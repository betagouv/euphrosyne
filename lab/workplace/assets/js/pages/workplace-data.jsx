import React from "react";
import { createRoot } from "react-dom/client";
import { QueryClientProvider, QueryClient } from "@tanstack/react-query";

import { ProcessedDataFileService } from "../processed-data/processed-data-file-service";
import { RawDataFileService } from "../raw-data/raw-data-file-service";
import { HDF5FileService } from "../hdf5/hdf5-file-service";

import FileManager from "../../../../assets/js/components/file-manager.jsx";
import HDF5TableActionCell from "../hdf5/hdf5-table-action-cell.jsx";

const queryClient = new QueryClient();

const RunTabPanel = ({ run, idx }) => {
  const rawService = new RawDataFileService(window.projectSlug, run.name);
  const processedService = new ProcessedDataFileService(
    window.projectSlug,
    run.name
  );
  const hdf5Service = new HDF5FileService(window.projectSlug, run.name);

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
            <FileManager
              title="HDF5"
              fileService={hdf5Service}
              cols={["name", "size"]}
              enableFormUpload={false}
              renderActionsCellFn={(file) => (
                <HDF5TableActionCell file={file} projectId={window.projectId} />
              )}
            />
          </div>
        </div>
      </div>
      <div className="fr-grid-row fr-grid-row--gutters">
        <div className="fr-col-12 fr-col-lg-6">
          <div className="fr-background-default--grey fr-p-3v">
            <FileManager
              title={window.gettext("Raw data")}
              fileService={rawService}
              cols={["name", "size"]}
              enableFormUpload={false}
            />
          </div>
        </div>
        <div className="fr-col-12 fr-col-lg-6">
          <div className="fr-background-default--grey fr-p-3v">
            <FileManager
              title={window.gettext("Processed data")}
              fileService={processedService}
              cols={["name", "size"]}
              enableFormUpload={false}
            />
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
