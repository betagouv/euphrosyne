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
  dataLabel: string;
  fileService: FileService;
  rootFiles: EuphrosyneFile[] | null;
  onRootFileDeleted: (fileName: string) => void;
  isSearchable?: boolean;
  displayedCols?: Col<EuphrosyneFile>[];
  actionCell?: React.ReactElement<"td">;
  canDelete?: boolean;
}

export default function WorkplaceDataTypeDisplay({
  dataLabel,
  fileService,
  rootFiles,
  onRootFileDeleted,
  displayedCols,
  isSearchable,
  actionCell,
  canDelete,
}: WorkplaceDataTypeDisplayProps) {
  const { project } = useWorkplaceContext();

  const [folderFiles, setFolderFiles] = useState<EuphrosyneFile[]>([]);
  const [isFolderLoading, setIsFolderLoading] = useState(false);
  const [folder, setFolder] = useState<string[]>([]);
  const isRootFolder = folder.length === 0;
  const displayedFiles = isRootFolder ? (rootFiles ?? []) : folderFiles;
  const isLoading = isRootFolder ? rootFiles === null : isFolderLoading;

  const appendFolder = (name: string) => {
    setFolder((prev) => [...prev, name]);
  };

  const removeLastFolder = () => {
    setFolder((prev) => prev.slice(0, -1));
  };

  useEffect(() => {
    if (isRootFolder) {
      return;
    }
    let isCurrent = true;
    setIsFolderLoading(true);
    fileService
      .listData(folder.join("/"))
      .then((files) => {
        if (isCurrent) {
          setFolderFiles(files);
          setIsFolderLoading(false);
        }
      })
      .catch((error) => {
        if (isCurrent) {
          console.error(`Failed to fetch workplace ${dataLabel}: ${error}`);
          setFolderFiles([]);
          setIsFolderLoading(false);
        }
      });
    return () => {
      isCurrent = false;
    };
  }, [dataLabel, fileService, folder, isRootFolder]);

  return (
    <div className="fr-background-default--grey">
      <h3>{dataLabel}</h3>
      <FileTable
        rows={displayedFiles}
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
              onDeleteSuccess={(fileName) => {
                if (isRootFolder) {
                  onRootFileDeleted(fileName);
                } else {
                  setFolderFiles((files) =>
                    files.filter((file) => file.name !== fileName),
                  );
                }
              }}
              fileService={fileService}
              onFolderOpen={appendFolder}
            />
          )
        }
      />
    </div>
  );
}
