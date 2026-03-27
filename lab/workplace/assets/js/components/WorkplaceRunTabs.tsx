import { useEffect, useState } from "react";
import { RawDataFileService } from "../raw-data/raw-data-file-service";
import { ProcessedDataFileService } from "../processed-data/processed-data-file-service";
import WorkplaceRunTab from "./WorkplaceRunTab";
import { LifecycleState, onLifecycleStateChanged } from "../lifecycle-state";
import { ProjectLifecycleSnapshot } from "../project-lifecycle-service";

export interface WorkplaceRunTabsProps {
  project: {
    name: string;
    slug: string;
    id: string;
  };
  isDataManagementEnabled: boolean;
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
  fetchProjectLifecyclePromise: Promise<ProjectLifecycleSnapshot>;
}

export default function WorkplaceRunTabs({
  runs,
  project,
  isDataManagementEnabled,
  fetchProjectLifecyclePromise,
}: WorkplaceRunTabsProps) {
  const t = {
    "Runs data": window.gettext("Runs data"),
    "Raw data": window.gettext("Raw data"),
    "Processed data": window.gettext("Processed data"),
  };

  const [selectedTabIndex, setSelectedTabIndex] = useState(0);
  const [lifecycleState, setLifecycleState] = useState<LifecycleState | null>(
    null,
  );

  useEffect(() => {
    let cancelled = false;

    fetchProjectLifecyclePromise
      .then((state) => {
        if (!cancelled) {
          setLifecycleState(state.lifecycleState);
        }
      })
      .catch((error) => {
        if (!cancelled) {
          console.error(error);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [fetchProjectLifecyclePromise]);

  useEffect(() => {
    if (!isDataManagementEnabled) {
      return;
    }

    return onLifecycleStateChanged(setLifecycleState);
  }, [isDataManagementEnabled]);

  const mutationsEnabled = !isDataManagementEnabled || lifecycleState === "HOT";

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
          id={`tabpanel-run-${run.id}-panel`}
          key={`run-tab-panel-${run.id}`}
          className={`fr-tabs__panel ${
            selectedTabIndex === index && "fr-tabs__panel--selected"
          }`}
          role="tabpanel"
          aria-labelledby={`tabpanel-run-${run.id}`}
          tabIndex={index}
        >
          <WorkplaceRunTab
            run={{
              ...run,
              rawDataTable: {
                ...run.rawDataTable,
                canDelete: run.rawDataTable.canDelete && mutationsEnabled,
              },
              processedDataTable: {
                ...run.processedDataTable,
                canDelete: run.processedDataTable.canDelete && mutationsEnabled,
              },
            }}
            project={project}
          />
        </div>
      ))}
    </div>
  );
}
