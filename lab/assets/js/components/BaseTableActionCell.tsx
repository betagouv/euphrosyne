import { displayMessage } from "../utils";
import { FileService } from "../file-service";
import { css } from "@emotion/react";
import { useContext } from "react";
import { FileContext } from "./FileContext";

interface BaseTableActionCellProps {
  fileService: FileService;
  canDelete: boolean;
  onDeleteSuccess?: (fileName: string) => void;
  setIsLoading?: (isLoading: boolean) => void;
}

const cellStyle = css({
  width: "150px",
});

export default function BaseTableActionCell({
  fileService,
  canDelete,
  onDeleteSuccess,
  setIsLoading,
}: BaseTableActionCellProps) {
  const file = useContext(FileContext);

  const downloadFile = async (path: string) => {
    const url = await fileService.fetchPresignedURL(path);
    window.open(url, "_blank");
  };

  const deleteFile = async (name: string, path: string) => {
    if (
      !window.confirm(
        window.interpolate(window.gettext("Delete the document %s ?"), [name])
      )
    ) {
      return;
    }
    setIsLoading && setIsLoading(true);
    try {
      await fileService.deleteFile(path);
    } catch (error) {
      displayMessage(
        window.interpolate(window.gettext("File %s could not be removed."), [
          name,
        ]),
        "error"
      );
      setIsLoading && setIsLoading(false);
    }
    if (onDeleteSuccess) onDeleteSuccess(name);
    setIsLoading && setIsLoading(false);
    displayMessage(
      window.interpolate(window.gettext("File %s has been removed."), [name]),
      "success"
    );
  };

  return (
    <td css={cellStyle}>
      {file && (
        <ul className="fr-btns-group fr-btns-group--inline fr-btns-group--sm">
          <li>
            <button
              className="download-btn fr-btn fr-icon-download-line fr-btn--secondary"
              onClick={() => downloadFile(file.path)}
            >
              {window.gettext("Download file")}
            </button>
          </li>
          {canDelete && (
            <li>
              <button
                className="delete-btn fr-btn fr-icon-delete-line fr-btn--secondary"
                onClick={() => deleteFile(file.name, file.path)}
              >
                {window.gettext("Delete file")}
              </button>
            </li>
          )}
        </ul>
      )}
    </td>
  );
}
