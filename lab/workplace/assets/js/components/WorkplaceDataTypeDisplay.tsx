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
  rootFiles: EuphrosyneFile[] | null;
  isSearchable?: boolean;
  displayedCols?: Col<EuphrosyneFile>[];
  actionCell?: React.ReactElement<"td">;
  canDelete?: boolean;
}

export default function WorkplaceDataTypeDisplay({
  dataLabel,
  fileService,
  rootFiles,
  displayedCols,
  isSearchable,
  actionCell,
  canDelete,
}: WorkplaceDataTypeDisplayProps) {
  const { project } = useWorkplaceContext();

  const [dataRows, setDataRows]: [
    EuphrosyneFile[],
    React.Dispatch<React.SetStateAction<EuphrosyneFile[]>>,
  ] = useState<EuphrosyneFile[]>(rootFiles ?? []);

  const [isLoading, setIsLoading] = useState(rootFiles === null);
  const [folder, setFolder] = useState<string[]>([]);

  const appendFolder = (name: string) => {
    setFolder((prev) => [...prev, name]);
  };

  const removeLastFolder = () => {
    setFolder((prev) => prev.slice(0, -1));
  };

  useEffect(() => {
    if (folder.length === 0) {
      setDataRows(rootFiles ?? []);
      setIsLoading(rootFiles === null);
      return;
    }
    let isCurrent = true;
    setIsLoading(true);
    fileService
      .listData(folder.join("/"))
      .then((files) => {
        if (isCurrent) {
          setDataRows(files);
          setIsLoading(false);
        }
      })
      .catch((error) => {
        if (isCurrent) {
          console.error(`Failed to fetch workplace ${dataLabel}: ${error}`);
          setDataRows([]);
          setIsLoading(false);
        }
      });
    return () => {
      isCurrent = false;
    };
  }, [dataLabel, fileService, folder, rootFiles]);

  return (
    <div className="fr-background-default--grey">
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
