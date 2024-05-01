import { css } from "@emotion/react";
import { useContext } from "react";
import { FileContext } from "./FileContext";
import { fileTableRowActionCellBtnStyle } from "./style";

interface BaseTableActionCellProps {
  onOpen: (name: string) => void;
}

const cellStyle = css({
  width: "150px",
});

export default function BaseTableActionCell({
  onOpen,
}: BaseTableActionCellProps) {
  const t = {
    Open: window.gettext("Open"),
  };
  const file = useContext(FileContext);

  return (
    <td css={cellStyle}>
      {file && (
        <ul className="fr-btns-group fr-btns-group--inline fr-btns-group--sm">
          <li>
            <button
              className="fr-btn fr-icon-arrow-right-line fr-btn--secondary"
              css={fileTableRowActionCellBtnStyle}
              onClick={() => onOpen(file.name)}
            >
              {t["Open"]}
            </button>
          </li>
        </ul>
      )}
    </td>
  );
}
