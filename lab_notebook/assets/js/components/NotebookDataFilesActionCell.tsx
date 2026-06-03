import { useContext } from "react";
import { FileContext } from "../../../../lab/assets/js/components/FileContext";
import BaseFileActionCell from "../../../../lab/assets/js/components/BaseFileActionCell";
import { FileService } from "../../../../lab/assets/js/file-service";

export default function NotebookDataFilesActionCell({
  projectId,
  fileService,
}: {
  projectId: string;
  fileService: FileService;
}) {
  const file = useContext(FileContext);

  if (!file || file.isDir) {
    return <td></td>;
  }

  return (
    <BaseFileActionCell
      projectId={projectId}
      fileService={fileService}
      canDelete={false}
    />
  );
}
