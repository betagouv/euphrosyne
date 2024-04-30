import { useEffect, useState } from "react";
import BaseTableActionCell from "../../../../assets/js/components/BaseTableActionCell";
import FileTable, { Col } from "../../../../assets/js/components/FileTable";
import {
  EuphrosyneFile,
  FileService,
} from "../../../../assets/js/file-service";
import { workplaceTableCols } from "../../../../assets/js/components/FileTableCols";

interface WorkplaceDataTypeDisplayProps {
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
  const [dataRows, setDataRows]: [
    EuphrosyneFile[],
    React.Dispatch<React.SetStateAction<EuphrosyneFile[]>>,
  ] = useState<EuphrosyneFile[]>([]);

  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    setIsLoading(true);
    fileService
      .listData()
      .then((files) => {
        setDataRows(files);
        setIsLoading(false);
      })
      .catch((error) => {
        console.error(`Failed to fetch workplace ${dataLabel}: ${error}`);
        setDataRows([]);
        setIsLoading(false);
      });
  }, []);

  return (
    <div className="fr-background-default--grey fr-p-3v">
      <h3>{dataLabel}</h3>
      <FileTable
        rows={dataRows}
        isLoading={isLoading}
        cols={displayedCols || workplaceTableCols}
        isSearchable={isSearchable}
        actionCell={
          actionCell || (
            <BaseTableActionCell
              canDelete={!!canDelete}
              onDeleteSuccess={(fileName) =>
                setDataRows(dataRows.filter((file) => file.name !== fileName))
              }
              fileService={fileService}
            />
          )
        }
      />
    </div>
  );
}
