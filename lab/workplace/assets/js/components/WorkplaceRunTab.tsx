import { RawDataFileService } from "../raw-data/raw-data-file-service";
import { ProcessedDataFileService } from "../processed-data/processed-data-file-service";
import HDF5FileTable from "../../../../hdf5/assets/js/components/HDF5FileTable";
import WorkplaceDataTypeDisplay from "./WorkplaceDataTypeDisplay";

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
    <div>
      {process.env.HDF5_ENABLE === "true" && (
        <div className="fr-grid-row fr-grid-row--gutters">
          <div className="fr-col-12">
            <div className="fr-background-default--grey fr-p-3v">
              <h3>HDF5</h3>
              <HDF5FileTable
                projectId={project.id}
                projectSlug={project.slug}
                runName={run.label}
              />
            </div>
          </div>
        </div>
      )}
      <div className="fr-grid-row fr-grid-row--gutters">
        <div className="fr-col-12 fr-col-lg-6">
          <WorkplaceDataTypeDisplay
            dataLabel={t["Raw data"]}
            fileService={run.rawDataFileService}
            isSearchable={true}
          />
        </div>
        <div className="fr-col-12 fr-col-lg-6">
          <WorkplaceDataTypeDisplay
            dataLabel={t["Processed data"]}
            fileService={run.processedDataFileService}
            isSearchable={true}
          />
        </div>
      </div>
    </div>
  );
}
