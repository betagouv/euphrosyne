import { displayMessage } from "../utils";
import { FileService } from "../file-service";
import { css } from "@emotion/react";
import { useContext } from "react";
import { FileContext } from "./FileContext";
import { fileTableRowActionCellBtnStyle } from "./style";

interface BaseFileActionCellProps {
  fileService: FileService;
  canDelete: boolean;
  onDeleteSuccess?: (fileName: string) => void;
  setIsLoading?: (isLoading: boolean) => void;
}

const cellStyle = css({
  width: "150px",
});

export default function BaseFileActionCell({
  fileService,
  canDelete,
  onDeleteSuccess,
  setIsLoading,
}: BaseFileActionCellProps) {
  const t = {
    "Delete the document %s ?": window.gettext("Delete the document %s ?"),
    "File %s could not be removed.": window.gettext(
      "File %s could not be removed.",
    ),
    "File %s has been removed.": window.gettext("File %s has been removed."),
    "Download file": window.gettext("Download file"),
    "Delete file": window.gettext("Delete file"),
  };
  const file = useContext(FileContext);

  const downloadFile = async (path: string) => {
    const url = await fileService.fetchPresignedURL(path);
    window.open(url, "_blank");
  };

  const deleteFile = async (name: string, path: string) => {
    if (
      !window.confirm(window.interpolate(t["Delete the document %s ?"], [name]))
    ) {
      return;
    }
    if (setIsLoading) setIsLoading(true);
    try {
      await fileService.deleteFile(path);
    } catch {
      displayMessage(
        window.interpolate(t["File %s could not be removed."], [name]),
        "error",
      );
      if (setIsLoading) setIsLoading(false);
    }
    if (onDeleteSuccess) onDeleteSuccess(name);
    if (setIsLoading) setIsLoading(false);
    displayMessage(
      window.interpolate(t["File %s has been removed."], [name]),
      "success",
    );
  };

  return (
    <td css={cellStyle}>
      {file && (
        <ul className="fr-btns-group fr-btns-group--inline fr-btns-group--sm">
          <li>
            <button
              className="fr-btn fr-icon-download-line fr-btn--secondary"
              css={fileTableRowActionCellBtnStyle}
              onClick={() => downloadFile(file.path)}
            >
              {t["Download file"]}
            </button>
          </li>
          {canDelete && (
            <li>
              <button
                className="fr-btn fr-icon-delete-line fr-btn--secondary"
                css={fileTableRowActionCellBtnStyle}
                onClick={() => deleteFile(file.name, file.path)}
              >
                {t["Delete file"]}
              </button>
            </li>
          )}
        </ul>
      )}
    </td>
  );
}
