import { FileService } from "../file-service";
import { useContext } from "react";
import { FileContext } from "./FileContext";
import BaseFileActionCell from "./BaseFileActionCell";
import BaseDirectoryActionCell from "./BaseDirectoryActionCell";

interface BaseTableActionCellProps {
  projectId: string;
  fileService: FileService;
  canDelete: boolean;
  onDeleteSuccess?: (fileName: string) => void;
  setIsLoading?: (isLoading: boolean) => void;
  onFolderOpen: (name: string) => void;
}

export default function BaseTableActionCell({
  projectId,
  fileService,
  canDelete,
  onDeleteSuccess,
  setIsLoading,
  onFolderOpen,
}: BaseTableActionCellProps) {
  const file = useContext(FileContext);
  return (
    <>
      {file &&
        (file.isDir ? (
          <BaseDirectoryActionCell onOpen={onFolderOpen} />
        ) : (
          <BaseFileActionCell
            projectId={projectId}
            fileService={fileService}
            canDelete={canDelete}
            onDeleteSuccess={onDeleteSuccess}
            setIsLoading={setIsLoading}
          />
        ))}
    </>
  );
}
