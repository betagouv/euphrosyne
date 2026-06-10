import { useEffect, useMemo, useState } from "react";
import { useClientContext } from "../../../../shared/js/EuphrosyneToolsClient.context";
import { useNotebookHDF5Context } from "../hdf5";
import { HDF5DatasetEntry } from "../hdf5";
import HDF5InlineVisualization from "./HDF5Visualization";

export default function MeasuringPointHDF5Entries({
  pointId,
}: {
  pointId: string;
}) {
  const {
    entriesByPointId,
    hasViewableHDF5DataByPointId,
    loadingEntriesByPointId,
  } = useNotebookHDF5Context();
  const toolsClient = useClientContext();
  const entries = entriesByPointId[pointId] || [];
  const hasViewableHDF5Data = !!hasViewableHDF5DataByPointId[pointId];
  const isLoading = !!loadingEntriesByPointId[pointId];
  const [selectedEntryId, setSelectedEntryId] = useState<string>("");
  const selectedEntry = useMemo(
    () => entries.find((entry) => entry.id === selectedEntryId) || null,
    [entries, selectedEntryId],
  );

  const t = {
    title: window.gettext("Associated viewable data"),
    detector: window.gettext("Detector"),
    loading: window.gettext("Loading associated HDF5 data..."),
    noData: window.gettext("No visualizable HDF5 data found for this point."),
  };

  useEffect(() => {
    if (entries.length === 0) {
      setSelectedEntryId("");
      return;
    }
    if (!entries.some((entry) => entry.id === selectedEntryId)) {
      setSelectedEntryId(entries[0].id);
    }
  }, [entries, selectedEntryId]);

  if (!hasViewableHDF5Data) {
    return null;
  }

  return (
    <section className="fr-mt-3w hdf5-point-section">
      <h5>{t.title}</h5>
      {isLoading ? (
        <p>{t.loading}</p>
      ) : entries.length === 0 ? (
        <p>{t.noData}</p>
      ) : (
        <>
          <div className="fr-select-group hdf5-detector-select">
            <label className="fr-label" htmlFor={`hdf5-detector-${pointId}`}>
              {t.detector}
            </label>
            <select
              className="fr-select"
              id={`hdf5-detector-${pointId}`}
              value={selectedEntryId}
              onChange={(event) =>
                setSelectedEntryId(event.currentTarget.value)
              }
            >
              {entries.map((entry) => (
                <option key={entry.id} value={entry.id}>
                  {getEntryDetectorLabel(entry, entries)}
                </option>
              ))}
            </select>
          </div>
          {selectedEntry && (
            <div className="hdf5-inline-visualization">
              <HDF5InlineVisualization
                entry={selectedEntry}
                fetchFn={toolsClient.fetchFn}
              />
            </div>
          )}
        </>
      )}
    </section>
  );
}

function getEntryDetectorLabel(
  entry: HDF5DatasetEntry,
  entries: HDF5DatasetEntry[],
): string {
  const label = getEntryDetectorName(entry);
  const hasDuplicateLabel =
    entries.filter((candidate) => getEntryDetectorName(candidate) === label)
      .length > 1;
  if (!hasDuplicateLabel) {
    return label;
  }
  return `${label} (${entry.fileName})`;
}

function getEntryDetectorName(entry: HDF5DatasetEntry): string {
  if (entry.dataKind === "map") {
    return entry.detectorName || entry.groupName;
  }
  return entry.datasetName;
}
