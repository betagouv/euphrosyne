import React from "react";
import { createRoot } from "react-dom/client";
import { QueryClientProvider, QueryClient } from "@tanstack/react-query";

import { ProcessedDataFileService } from "../processed-data/processed-data-file-service";
import { RawDataFileService } from "../raw-data/raw-data-file-service";

import FileTable from "../../../../assets/js/components/file-table.jsx";

const queryClient = new QueryClient();

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
            <FileTable service={rawService} cols={["name", "size"]} />
          </div>
        </div>
        <div className="fr-col-12 fr-col-lg-6">
          <div className="fr-background-default--grey fr-p-3v">
            <h3>{window.gettext("Processed data")}</h3>
            <FileTable service={processedService} cols={["name", "size"]} />
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
