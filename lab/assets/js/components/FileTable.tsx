import { useState } from "react";
import { FileProvider } from "./FileContext";
import { EuphrosyneFile } from "../file-service";
import { css } from "@emotion/react";
import { loadingDivStyle } from "./style";

export interface Col<T> {
  label: string;
  key: keyof T;
  formatter?: (value: string | null) => string;
}

interface FileTableProps {
  rows: EuphrosyneFile[];
  cols: Col<EuphrosyneFile>[];
  folder?: string[];
  isLoading?: boolean;
  isSearchable?: boolean;
  actionCell?: React.ReactElement<"td">;
  onPreviousFolderClick?: () => void;
}

const COLLAPSED_ROW_NUM = 25;

const fileTableStyle = css({
  width: "100%",
});

const cellStyle = css({
  verticalAlign: "middle",
});

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
  folder,
  isLoading,
  isSearchable,
  actionCell,
  onPreviousFolderClick,
}: FileTableProps) {
  const t = {
    Filter: window.gettext("Filter"),
    "No file yet": window.gettext("No file yet"),
    "%s results": window.gettext("%s results"),
    "Show less": window.gettext("Show less"),
    "Show more": window.gettext("Show more"),
  };

  const [isExpanded, setIsExpanded] = useState(false);
  const [filterText, setFilterText] = useState("");

  const numCols = actionCell ? cols.length + 1 : cols.length;

  const filteredRows = rows.filter((row) =>
    filterText !== ""
      ? row.name.toLowerCase().includes(filterText.toLowerCase())
      : true,
  );

  const displayedRows = isExpanded
    ? filteredRows
    : filteredRows.slice(0, COLLAPSED_ROW_NUM);

  const filterInputId = "search-" + Math.random().toString(36).substring(2, 16);

  return (
    <>
      {isSearchable && (
        <div className="fr-mb-1w">
          <div className="fr-search-bar" id="header-search" role="search">
            <label className="fr-label" htmlFor={filterInputId}>
              {t["Filter"]}
            </label>
            <input
              className="fr-input"
              placeholder={t["Filter"]}
              type="search"
              id={filterInputId}
              onInput={(e) =>
                setFilterText((e.target as HTMLInputElement).value)
              }
            />
            <button className="fr-btn" title={t["Filter"]}>
              {t["Filter"]}
            </button>
          </div>
          <p className="fr-hint-text">
            {window.interpolate(t["%s results"], [
              (filterText === ""
                ? rows.length
                : filteredRows.length
              ).toString(),
            ])}
          </p>
        </div>
      )}
      {folder && folder.length > 0 && (
        <div
          css={css({
            display: "flex",
            justifyItems: "center",
            alignItems: "center",
          })}
          className="fr-mb-1w"
        >
          <button
            className="fr-btn fr-icon-arrow-left-line fr-btn--sm fr-btn--secondary fr-mr-1w"
            onClick={onPreviousFolderClick}
          />
          <div>/{folder.join("/")}</div>
        </div>
      )}
      <table className="fr-table" css={fileTableStyle}>
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
              {[...Array(numCols)].map((_, i) => (
                <td key={`loading-cell-${i}`} css={cellStyle}>
                  <div css={loadingDivStyle}>&nbsp;</div>
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
                        <td key={`file-table-cell-${col.key}`} css={cellStyle}>
                          {col.formatter
                            ? col.formatter((row[col.key] || "").toString())
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
                  <td colSpan={numCols} css={[cellStyle, noDataCellStyle]}>
                    {t["No file yet"]}
                  </td>
                </tr>
              )}
            </>
          )}
        </tbody>
        {filteredRows.length > COLLAPSED_ROW_NUM && (
          <tfoot>
            <tr>
              <td colSpan={numCols} style={{ width: "100%" }} css={cellStyle}>
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
                    ? t["Show less"]
                    : t["Show more"] +
                      ` (${isLoading ? 0 : filteredRows.length - COLLAPSED_ROW_NUM})`}
                </button>
              </td>
            </tr>
          </tfoot>
        )}
      </table>
    </>
  );
}
