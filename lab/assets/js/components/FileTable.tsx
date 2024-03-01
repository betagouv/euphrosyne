import { useState } from "react";
import { FileProvider } from "./FileContext";
import { EuphrosyneFile } from "../file-service";
import { css } from "@emotion/react";

export interface Col<T> {
  label: string;
  key: keyof T;
  formatter?: (value: string) => string;
}

interface FileTableProps {
  rows: EuphrosyneFile[];
  cols: Col<EuphrosyneFile>[];
  isLoading?: boolean;
  actionCell?: React.ReactElement<"td">;
}

const COLLAPSED_ROW_NUM = 25;

const noDataCellStyle = css({
  "&&": {
    textAlign: "center",
  },
});

const theadCellStyle = css({
  "&&": { fontSize: "0.6875rem" },
});

export default function FileTable({
  cols,
  rows,
  isLoading,
  actionCell,
}: FileTableProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const numCols = actionCell ? cols.length : cols.length + 1;

  const displayedRows = isExpanded ? rows : rows.slice(0, COLLAPSED_ROW_NUM);

  return (
    <table className="file-table fr-table">
      <thead>
        <tr>
          {cols.map(({ label }) => (
            <th
              scope="col"
              key={`file-table-head-${label}`}
              css={theadCellStyle}
            >
              {label}
            </th>
          ))}
          {actionCell && <th scope="col"></th>}
        </tr>
      </thead>
      <tbody>
        {isLoading ? (
          <tr className="loading">
            {[...Array(numCols + 1)].map((_, i) => (
              <td key={`loading-cell-${i}`}>
                <div>&nbsp;</div>
              </td>
            ))}
          </tr>
        ) : (
          <>
            {rows.length !== 0 ? (
              <>
                {displayedRows.map((row, i) => (
                  <tr key={`file-table-row-${i}`}>
                    {cols.map((col) => (
                      <td key={`file-table-cell-${col.key}`}>
                        {col.formatter
                          ? col.formatter(row[col.key].toString())
                          : String(row[col.key])}
                      </td>
                    ))}
                    {actionCell && (
                      <FileProvider value={row}>{actionCell}</FileProvider>
                    )}
                  </tr>
                ))}
              </>
            ) : (
              <tr className="no_data">
                <td colSpan={numCols} css={noDataCellStyle}>
                  {window.gettext("No file yet")}
                </td>
              </tr>
            )}
          </>
        )}
      </tbody>
      {rows.length > COLLAPSED_ROW_NUM && (
        <tfoot>
          <tr>
            <td colSpan={numCols} style={{ width: "100%" }}>
              <button
                className={`fr-btn fr-btn--tertiary-no-outline fr-btn--sm fr-btn--icon-left ${
                  isExpanded
                    ? "fr-icon-arrow-up-s-line"
                    : "fr-icon-arrow-down-s-line"
                }`}
                style={{ justifyContent: "center", width: "100%" }}
                aria-expanded={isExpanded}
                onClick={() => setIsExpanded(!isExpanded)}
              >
                {isExpanded
                  ? window.gettext("Show less")
                  : window.gettext("Show more") +
                    ` (${rows.length - COLLAPSED_ROW_NUM})`}
              </button>
            </td>
          </tr>
        </tfoot>
      )}
    </table>
  );
}
