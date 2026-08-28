import { useState } from "react";
import type { EuphrosyneFile } from "../../../../assets/js/file-service";
import { findVisualizableDataFiles } from "../../../../data_visualization/assets/js/data-visualization-service";
import DataVisualizationAssistant from "../../../../data_visualization/assets/js/components/DataVisualizationAssistant";
import { RawDataFileService } from "../raw-data/raw-data-file-service";
import { ProcessedDataFileService } from "../processed-data/processed-data-file-service";
import WorkplaceDataTypeDisplay from "./WorkplaceDataTypeDisplay";
import { WorkplaceContext } from "./WorkplaceContext";

export interface WorkplaceRunTabProps {
  project: {
    name: string;
    slug: string;
    id: string;
  };
  run: {
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
  };
}

export default function WorkplaceRunTab({
  run,
  project,
}: WorkplaceRunTabProps) {
  const [rawDataFiles, setRawDataFiles] = useState<EuphrosyneFile[] | null>(
    null,
  );
  const [processedDataFiles, setProcessedDataFiles] = useState<
    EuphrosyneFile[] | null
  >(null);
  const t = {
    "Runs data": window.gettext("Runs data"),
    "Raw data": window.gettext("Raw data"),
    "Processed data": window.gettext("Processed data"),
    "Open run lab notebook": window.gettext("Open run lab notebook"),
  };
  const visualizableDataFiles =
    rawDataFiles && processedDataFiles
      ? findVisualizableDataFiles([...rawDataFiles, ...processedDataFiles])
      : [];

  return (
    <WorkplaceContext.Provider value={{ project }}>
      <div>
        <div className="fr-grid-row fr-grid-row--gutters">
          <div className="fr-col-12">
            <a
              className="fr-link fr-link--lg"
              target="_blank"
              rel="noreferrer"
              href={`/lab/run/${run.id}/notebook`}
            >
              {t["Open run lab notebook"]}
            </a>
            <DataVisualizationAssistant
              projectSlug={project.slug}
              files={visualizableDataFiles}
              fetchFn={run.rawDataFileService.fetchFn}
            />
          </div>
          <div className="fr-col-12 fr-col-lg-6">
            <WorkplaceDataTypeDisplay
              projectId={project.id}
              dataLabel={t["Raw data"]}
              fileService={run.rawDataFileService}
              canDelete={run.rawDataTable.canDelete}
              isSearchable={true}
              onRootFilesLoaded={setRawDataFiles}
            />
          </div>
          <div className="fr-col-12 fr-col-lg-6">
            <WorkplaceDataTypeDisplay
              projectId={project.id}
              dataLabel={t["Processed data"]}
              fileService={run.processedDataFileService}
              canDelete={run.processedDataTable.canDelete}
              isSearchable={true}
              onRootFilesLoaded={setProcessedDataFiles}
            />
          </div>
        </div>
      </div>
    </WorkplaceContext.Provider>
  );
}
