import { useNotebookHDF5Context } from "../hdf5";

export default function MeasuringPointHDF5Entries({
  pointId,
}: {
  pointId: string;
}) {
  const {
    entriesByPointId,
    hasMatchesByPointId,
    loadingEntriesByPointId,
    spectrumModalId,
    visualizeEntry,
  } = useNotebookHDF5Context();
  const entries = entriesByPointId[pointId] || [];
  const hasMatches = !!hasMatchesByPointId[pointId];
  const isLoading = !!loadingEntriesByPointId[pointId];

  const t = {
    title: window.gettext("Associated viewable data"),
    hint: window.gettext("Select an entry to visualize the associated data."),
    entry: window.gettext("Data"),
    type: window.gettext("Type"),
    sourceFile: window.gettext("Source file"),
    information: window.gettext("Information"),
    action: window.gettext("Action"),
    visualize: window.gettext("Visualize"),
    loading: window.gettext("Loading associated HDF5 data..."),
    noData: window.gettext("No visualizable HDF5 data found for this point."),
  };

  if (!hasMatches) {
    return null;
  }

  return (
    <section className="fr-mt-3w hdf5-point-section">
      <h5>{t.title}</h5>
      <p className="fr-hint-text">{t.hint}</p>
      {isLoading ? (
        <p>{t.loading}</p>
      ) : entries.length === 0 ? (
        <p>{t.noData}</p>
      ) : (
        <div className="fr-table fr-table--no-caption hdf5-table hdf5-point-table">
          <div className="fr-table__wrapper">
            <div className="fr-table__container">
              <div className="fr-table__content">
                <table>
                  <caption>{t.title}</caption>
                  <thead>
                    <tr>
                      <th scope="col">{t.entry}</th>
                      <th scope="col">{t.type}</th>
                      <th scope="col">{t.sourceFile}</th>
                      <th scope="col">{t.information}</th>
                      <th scope="col" className="hdf5-table__action">
                        {t.action}
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {entries.map((entry) => (
                      <tr key={entry.id}>
                        <td>
                          <span>{entry.datasetName}</span>
                        </td>
                        <td>{entry.dataKindLabel}</td>
                        <td>{entry.fileName}</td>
                        <td>{entry.metadataSummary}</td>
                        <td className="hdf5-table__action">
                          <button
                            type="button"
                            className="fr-btn fr-btn--sm fr-btn--tertiary-no-outline fr-btn--icon-left fr-icon-eye-line"
                            aria-controls={spectrumModalId}
                            data-fr-opened={false}
                            onClick={() => visualizeEntry(entry)}
                          >
                            {t.visualize}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
