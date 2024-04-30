import { useState } from "react";
import { RawDataFileService } from "../raw-data/raw-data-file-service";
import { ProcessedDataFileService } from "../processed-data/processed-data-file-service";
import WorkplaceRunTab from "./WorkplaceRunTab";

export interface WorkplaceRunTabsProps {
  project: {
    name: string;
    slug: string;
    id: string;
  };
  runs: {
    id: string;
    label: string;
    rawDataTable: {
      canDelete: boolean;
    };
    processedDataTable: {
      canDelete: boolean;
    };
    rawDataFileService: RawDataFileService;
    processedDataFileService: ProcessedDataFileService;
  }[];
}

export default function WorkplaceRunTabs({
  runs,
  project,
}: WorkplaceRunTabsProps) {
  const t = {
    "Runs data": window.gettext("Runs data"),
    "Raw data": window.gettext("Raw data"),
    "Processed data": window.gettext("Processed data"),
  };

  const [selectedTabIndex, setSelectedTabIndex] = useState(0);

  return (
    <div className="fr-tabs">
      <ul className="fr-tabs__list" role="tablist" aria-label={t["Runs data"]}>
        {runs.map((run, index) => (
          <li role="presentation" key={`run-tab-${run.id}`}>
            <button
              id="tabpanel-run-{{ run.id }}"
              className="fr-tabs__tab fr-icon-checkbox-line fr-tabs__tab--icon-left"
              tabIndex={index}
              role="tab"
              aria-selected={selectedTabIndex === index}
              aria-controls={`tabpanel-run-${run.id}-panel`}
              onClick={() => setSelectedTabIndex(index)}
            >
              {run.label}
            </button>
          </li>
        ))}
      </ul>
      {runs.map((run, index) => (
        <div
          id="tabpanel-run-{{ run.id }}-panel"
          key={`run-tab-panel-${run.id}`}
          className={`fr-tabs__panel ${
            selectedTabIndex === index && "fr-tabs__panel--selected"
          }`}
          role="tabpanel"
          aria-labelledby={`tabpanel-run-${run.id}`}
          tabIndex={index}
        >
          <WorkplaceRunTab run={run} project={project} />
        </div>
      ))}
    </div>
  );
}
