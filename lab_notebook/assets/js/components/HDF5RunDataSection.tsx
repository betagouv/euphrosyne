import { HDF5FileSummary } from "../hdf5";
import { formatBytes } from "../../../../lab/assets/js/utils.js";

function formatDate(date: Date): string {
  if (Number.isNaN(date.getTime())) {
    return "";
  }
  return date.toLocaleString();
}

export default function HDF5RunDataSection({
  projectId,
  fileSummaries,
  isLoading,
  error,
}: {
  projectId: string;
  fileSummaries: HDF5FileSummary[];
  isLoading: boolean;
  error: string | null;
}) {
  const t = {
    title: window.gettext("Available viewable files for this run"),
    hint: window.gettext(
      "Viewable data has been detected automatically from the run files. Expand a measurement point below to visualize the associated spectra.",
    ),
    file: window.gettext("HDF5 file"),
    entries: window.gettext("Entries (groups)"),
    coveredPoints: window.gettext("Covered points"),
    modified: window.gettext("Modified"),
    size: window.gettext("Size"),
    action: window.gettext("Action"),
    explore: window.gettext("Explore"),
    loading: window.gettext("Loading HDF5 data..."),
    noData: window.gettext("No HDF5 data available for this run."),
    unknown: window.gettext("Unknown"),
  };

  return (
    <>
      <h4>{t.title}</h4>
      <p className="fr-text--sm">{t.hint}</p>
      {error && (
        <div className="fr-alert fr-alert--error fr-alert--sm fr-mb-2w">
          <p>{error}</p>
        </div>
      )}
      {isLoading ? (
        <p>{t.loading}</p>
      ) : fileSummaries.length === 0 ? (
        <p>{t.noData}</p>
      ) : (
        <div className="fr-table fr-table--no-caption hdf5-table">
          <div className="fr-table__wrapper">
            <div className="fr-table__container">
              <div className="fr-table__content">
                <table>
                  <caption>{t.title}</caption>
                  <thead>
                    <tr>
                      <th scope="col">{t.file}</th>
                      <th scope="col">{t.entries}</th>
                      <th scope="col">{t.coveredPoints}</th>
                      <th scope="col">{t.modified}</th>
                      <th scope="col">{t.size}</th>
                      <th scope="col" className="hdf5-table__action">
                        {t.action}
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {fileSummaries.map(
                      ({ file, entryCount, coveredPointRange }) => (
                        <tr key={file.path}>
                          <td>
                            <span
                              className="fr-icon-file-line fr-icon--sm hdf5-file-icon"
                              aria-hidden="true"
                            />
                            <span>{file.name}</span>
                          </td>
                          <td>{entryCount ?? t.unknown}</td>
                          <td>{coveredPointRange || "-"}</td>
                          <td>{formatDate(file.lastModified)}</td>
                          <td>
                            {file.size === null ? "-" : formatBytes(file.size)}
                          </td>
                          <td className="hdf5-table__action">
                            <a
                              className="fr-link fr-icon-external-link-line fr-link--icon-right"
                              href={`/lab/project/${projectId}/hdf5-viewer?file=${encodeURIComponent(file.path)}`}
                            >
                              {t.explore}
                            </a>
                          </td>
                        </tr>
                      ),
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
