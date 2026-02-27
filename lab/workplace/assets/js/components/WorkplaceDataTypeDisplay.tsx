import { useEffect, useState } from "react";
import BaseTableActionCell from "../../../../assets/js/components/BaseTableActionCell";
import FileTable, { Col } from "../../../../assets/js/components/FileTable";
import {
  EuphrosyneFile,
  FileService,
} from "../../../../assets/js/file-service";
import { workplaceTableCols } from "../../../../assets/js/components/FileTableCols";
import { useWorkplaceContext } from "./WorkplaceContext";

interface WorkplaceDataTypeDisplayProps {
  projectId: string;
  dataLabel: string;
  fileService: FileService;
  isSearchable?: boolean;
  displayedCols?: Col<EuphrosyneFile>[];
  actionCell?: React.ReactElement<"td">;
  canDelete?: boolean;
}

export default function WorkplaceDataTypeDisplay({
  dataLabel,
  fileService,
  displayedCols,
  isSearchable,
  actionCell,
  canDelete,
}: WorkplaceDataTypeDisplayProps) {
  const { project } = useWorkplaceContext();

  const [dataRows, setDataRows]: [
    EuphrosyneFile[],
    React.Dispatch<React.SetStateAction<EuphrosyneFile[]>>,
  ] = useState<EuphrosyneFile[]>([]);

  const [isLoading, setIsLoading] = useState(false);
  const [folder, setFolder] = useState<string[]>([]);

  const appendFolder = (name: string) => {
    setFolder((prev) => [...prev, name]);
  };

  const removeLastFolder = () => {
    setFolder((prev) => prev.slice(0, -1));
  };

  useEffect(() => {
    setIsLoading(true);
    fileService
      .listData(folder.join("/"))
      .then((files) => {
        setDataRows(files);
        setIsLoading(false);
      })
      .catch((error) => {
        console.error(`Failed to fetch workplace ${dataLabel}: ${error}`);
        setDataRows([]);
        setIsLoading(false);
      });
  }, [folder]);

  return (
    <div className="fr-background-default--grey fr-p-3v">
      <h3>{dataLabel}</h3>
      <FileTable
        rows={dataRows}
        isLoading={isLoading}
        cols={displayedCols || workplaceTableCols}
        isSearchable={isSearchable}
        folder={folder}
        onPreviousFolderClick={removeLastFolder}
        actionCell={
          actionCell || (
            <BaseTableActionCell
              projectId={project.id}
              canDelete={!!canDelete}
              onDeleteSuccess={(fileName) =>
                setDataRows(dataRows.filter((file) => file.name !== fileName))
              }
              fileService={fileService}
              onFolderOpen={appendFolder}
            />
          )
        }
      />
    </div>
  );
}
