import { useContext, useEffect, useState } from "react";
import { FileContext } from "../../../../assets/js/components/FileContext";
import { EuphrosyneFile } from "../../../../assets/js/file-service";
import { workplaceTableCols } from "../../../../assets/js/components/FileTableCols";
import { HDF5FileService } from "../hdf5-file.service";
import FileTable from "../../../../assets/js/components/FileTable";

interface HDF5FileTableProps {
  projectId: string;
  projectSlug: string;
  runName: string;
}

function HDF5TableActionCell({ projectId }: { projectId: string }) {
  const t = {
    "View file": window.gettext("View file"),
  };

  const file = useContext(FileContext);

  return (
    <td>
      {file && (
        <ul className="fr-btns-group fr-btns-group--inline fr-btns-group--sm">
          <li>
            <a
              className="fr-btn fr-icon-eye-line fr-btn--secondary"
              href={`/lab/project/${projectId}/hdf5-viewer?file=${file.path}`}
            >
              {t["View file"]}
            </a>
          </li>
        </ul>
      )}
    </td>
  );
}

export default function HDF5FileTable({
  projectId,
  projectSlug,
  runName,
}: HDF5FileTableProps) {
  const [files, setFiles] = useState<EuphrosyneFile[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fileService = new HDF5FileService(projectSlug, runName);
    setIsLoading(true);
    fileService
      .listData()
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
      actionCell={<HDF5TableActionCell projectId={projectId} />}
    />
  );
}
