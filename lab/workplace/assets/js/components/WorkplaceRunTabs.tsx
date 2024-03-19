import { useEffect, useState } from "react";
import FileTable, { Col } from "../../../../assets/js/components/FileTable";
import { RawDataFileService } from "../raw-data/raw-data-file-service";
import { ProcessedDataFileService } from "../processed-data/processed-data-file-service";
import { EuphrosyneFile } from "../../../../assets/js/file-service";
import { formatBytes } from "../../../../assets/js/utils";
import BaseTableActionCell from "../../../../assets/js/components/BaseTableActionCell";

const tableCols: Col<EuphrosyneFile>[] = [
  { label: window.gettext("File"), key: "name" },
  {
    label: window.gettext("Size"),
    key: "size",
    formatter: (value: string) => formatBytes(parseInt(value)),
  },
];

export interface WorkplaceRunTabsProps {
  project: {
    name: string;
    slug: string;
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

export default function WorkplaceRunTabs({ runs }: WorkplaceRunTabsProps) {
  const t = {
    "Runs data": window.gettext("Runs data"),
    "Raw data": window.gettext("Raw data"),
    "Processed data": window.gettext("Processed data"),
  };

  const [selectedTabIndex, setSelectedTabIndex] = useState(0);
  const runRawData: [
    EuphrosyneFile[],
    React.Dispatch<React.SetStateAction<EuphrosyneFile[]>>
  ][] = runs.map(() => useState<EuphrosyneFile[]>([]));
  const runProcessedData: [
    EuphrosyneFile[],
    React.Dispatch<React.SetStateAction<EuphrosyneFile[]>>
  ][] = runs.map(() => useState<EuphrosyneFile[]>([]));
  const rawLoadingStates = runs.map(() => useState(false));
  const processedLoadingStates = runs.map(() => useState(false));

  useEffect(() => {
    runRawData.forEach(async ([, setFiles], index) => {
      const files = await runs[index].rawDataFileService.listData();
      setFiles(files);
      rawLoadingStates[index][1](false);
    });
    runProcessedData.forEach(async ([, setFiles], index) => {
      const files = await runs[index].processedDataFileService.listData();
      setFiles(files);
      processedLoadingStates[index][1](false);
    });
  }, []);
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
          <div className="fr-grid-row fr-grid-row--gutters">
            <div className="fr-col-12 fr-col-lg-6">
              <div className="fr-background-default--grey fr-p-3v">
                <h3>{t["Raw data"]}</h3>
                <FileTable
                  rows={runRawData[index][0]}
                  isLoading={rawLoadingStates[index][0]}
                  cols={tableCols}
                  isSearchable={true}
                  actionCell={
                    <BaseTableActionCell
                      canDelete={run.rawDataTable.canDelete}
                      onDeleteSuccess={(fileName) =>
                        runRawData[index][1](
                          runRawData[index][0].filter(
                            (file) => file.name !== fileName
                          )
                        )
                      }
                      fileService={run.rawDataFileService}
                    />
                  }
                />
              </div>
            </div>
            <div className="fr-col-12 fr-col-lg-6">
              <div className="fr-background-default--grey fr-p-3v">
                <h3>{t["Processed data"]}</h3>
                <FileTable
                  rows={runProcessedData[index][0]}
                  isLoading={processedLoadingStates[index][0]}
                  cols={tableCols}
                  isSearchable={true}
                  actionCell={
                    <BaseTableActionCell
                      canDelete={run.processedDataTable.canDelete}
                      onDeleteSuccess={(fileName) =>
                        runProcessedData[index][1](
                          runProcessedData[index][0].filter(
                            (file) => file.name !== fileName
                          )
                        )
                      }
                      fileService={run.processedDataFileService}
                    />
                  }
                />
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
