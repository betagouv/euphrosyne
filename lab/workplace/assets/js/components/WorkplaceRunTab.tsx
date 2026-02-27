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
  const t = {
    "Runs data": window.gettext("Runs data"),
    "Raw data": window.gettext("Raw data"),
    "Processed data": window.gettext("Processed data"),
  };

  return (
    <WorkplaceContext.Provider value={{ project }}>
      <div>
        <div className="fr-grid-row fr-grid-row--gutters">
          <div className="fr-col-12 fr-col-lg-6">
            <WorkplaceDataTypeDisplay
              projectId={project.id}
              dataLabel={t["Raw data"]}
              fileService={run.rawDataFileService}
              isSearchable={true}
            />
          </div>
          <div className="fr-col-12 fr-col-lg-6">
            <WorkplaceDataTypeDisplay
              projectId={project.id}
              dataLabel={t["Processed data"]}
              fileService={run.processedDataFileService}
              isSearchable={true}
            />
          </div>
        </div>
      </div>
    </WorkplaceContext.Provider>
  );
}
