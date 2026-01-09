import { useContext, useEffect, useState } from "react";
import { FileContext } from "../../../../assets/js/components/FileContext";
import { EuphrosyneFile } from "../../../../assets/js/file-service";
import { workplaceTableCols } from "../../../../assets/js/components/FileTableCols";
import { HDF5FileService } from "../hdf5-file.service";
import FileTable from "../../../../assets/js/components/FileTable";
import BaseDirectoryActionCell from "../../../../assets/js/components/BaseDirectoryActionCell";
import toolsFetch from "../../../../../shared/js/euphrosyne-tools-client";

interface HDF5FileTableProps {
  projectSlug: string;
  runName: string;
}

function HDF5TableActionCell({
  onDirectoryOpen,
}: {
  onDirectoryOpen: (name: string) => void;
}) {
  const file = useContext(FileContext);

  return (
    <td>
      {file?.isDir ? (
        <BaseDirectoryActionCell onOpen={onDirectoryOpen} />
      ) : null}
    </td>
  );
}

export default function HDF5FileTable({
  projectSlug,
  runName,
}: HDF5FileTableProps) {
  const [files, setFiles] = useState<EuphrosyneFile[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [folder, setFolder] = useState<string[]>([]);

  const appendFolder = (name: string) => {
    setFolder((prev) => [...prev, name]);
  };

  const removeLastFolder = () => {
    setFolder((prev) => prev.slice(0, -1));
  };

  useEffect(() => {
    const fileService = new HDF5FileService(projectSlug, runName, toolsFetch);
    setIsLoading(true);
    fileService
      .listData(folder.join("/"))
      .then((files) => {
        setFiles(files);
        setIsLoading(false);
      })
      .catch(() => {
        setFiles([]);
        setIsLoading(false);
      });
  }, [projectSlug, runName]);

  return (
    <FileTable
      rows={files}
      cols={workplaceTableCols}
      isLoading={isLoading}
      folder={folder}
      onPreviousFolderClick={removeLastFolder}
      actionCell={
        <HDF5TableActionCell onDirectoryOpen={appendFolder} />
      }
    />
  );
}
