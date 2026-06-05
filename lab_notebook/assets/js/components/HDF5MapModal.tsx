import { css } from "@emotion/react";
import {
  ChangeEvent,
  Component,
  ReactNode,
  Suspense,
  use,
  useEffect,
  useMemo,
  useState,
} from "react";
import { HeatmapVis, useDomain } from "@witoldw/h5web-lib";

import {
  assertArrayShape,
  assertDataset,
  assertNumericType,
  H5GroveProvider,
  useDataContext,
  useDatasetValue,
  useEntity,
  useNdArray,
  useToNumArray,
} from "@witoldw/h5web-app";
import {
  buildScientificMetadataRows,
  createToolsH5GroveFetcher,
  HDF5DatasetEntry,
  ScientificMetadataRow,
  ToolsFetch,
} from "../hdf5";
import HDF5DataLoadingIndicator from "./HDF5DataLoadingIndicator";
import HDF5MetadataPanel from "./HDF5MetadataPanel";
import HDF5SpectrumPlot from "./HDF5SpectrumPlot";

const modalContentStyle = css({
  minHeight: "calc(100vh - 8rem)",
});

const modalContainerStyle = css({
  maxWidth: "none",
  width: "calc(100vw - 2rem)",
  "@media (max-width: 48rem)": {
    width: "100vw",
  },
});

const visualizationLayoutStyle = css({
  display: "grid",
  gridTemplateColumns: "minmax(15rem, 18rem) minmax(0, 1fr)",
  minHeight: "calc(100vh - 14rem)",
  border: "1px solid var(--border-default-grey)",
  borderRadius: "0.5rem",
  overflow: "hidden",
  "@media (max-width: 62rem)": {
    gridTemplateColumns: "1fr",
  },
});

const metadataPanelStyle = css({
  borderRight: "1px solid var(--border-default-grey)",
  padding: "1rem 1.25rem",
  background: "var(--background-alt-grey)",
  "@media (max-width: 62rem)": {
    borderRight: "none",
    borderBottom: "1px solid var(--border-default-grey)",
  },
});

const rangeControlsStyle = css({
  display: "grid",
  gridTemplateColumns: "1fr 1fr",
  gap: "0.5rem",
  marginTop: "0.75rem",
  "@media (max-width: 36rem)": {
    gridTemplateColumns: "1fr",
  },
});

const mainPanelStyle = css({
  display: "flex",
  flexDirection: "column",
  gap: "1rem",
  minWidth: 0,
  padding: "1rem 1.25rem",
});

const visualizationLoadingStyle = css({
  alignItems: "center",
  display: "flex",
  minHeight: "24rem",
});

const spectrumAreaStyle = css({
  display: "grid",
  gridTemplateColumns: "minmax(34rem, 1fr) minmax(14rem, 17rem)",
  gap: "1rem",
  alignItems: "stretch",
  "@media (max-width: 78rem)": {
    gridTemplateColumns: "1fr",
  },
});

const sectionStyle = css({
  minWidth: 0,
});

const sectionTitleStyle = css({
  alignItems: "center",
  display: "flex",
  gap: "0.5rem",
  marginBottom: "0.5rem",
});

const rangeCardStyle = css({
  alignSelf: "start",
  border: "1px solid var(--border-default-grey)",
  borderRadius: "0.5rem",
  padding: "1rem",
});

const rangeFieldsetStyle = css({
  display: "grid",
  gap: "0.5rem",
  margin: 0,
  minWidth: 0,
});

const rangeHintStyle = css({
  gridColumn: "1 / -1",
  margin: 0,
});

const rangeActionRowStyle = css({
  display: "flex",
  gridColumn: "1 / -1",
  marginTop: "0.25rem",
  width: "100%",
});

const rangeButtonStyle = css({
  justifyContent: "center",
  width: "100%",
});

const helpCardStyle = css({
  background: "var(--background-alt-blue-france)",
  border: "1px solid var(--border-default-blue-france)",
  borderRadius: "0.5rem",
  color: "var(--text-default-grey)",
  fontSize: "0.875rem",
  lineHeight: 1.5,
  marginTop: "0.5rem",
  padding: "0.75rem",
});

const mapSectionStyle = css({
  borderTop: "1px solid var(--border-default-grey)",
  paddingTop: "1rem",
});

const plotStyle = css({
  height: "clamp(18rem, 32vh, 25rem)",
  minHeight: "18rem",
  width: "100%",
});

const mapStyle = css({
  height: "clamp(30rem, 52vh, 44rem)",
  minHeight: "30rem",
  width: "100%",
});

const summaryFooterStyle = css({
  alignItems: "center",
  border: "1px solid var(--border-default-grey)",
  borderRadius: "0.25rem",
  display: "flex",
  flexWrap: "wrap",
  gap: "0.5rem 1rem",
  padding: "0.5rem 0.75rem",
});

const summaryItemStyle = css({
  color: "var(--text-mention-grey)",
  fontSize: "0.875rem",
  whiteSpace: "nowrap",
});

interface HDF5MapErrorBoundaryProps {
  children: ReactNode;
}

class HDF5MapErrorBoundary extends Component<
  HDF5MapErrorBoundaryProps,
  { error: Error | null }
> {
  constructor(props: HDF5MapErrorBoundaryProps) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { error };
  }

  render() {
    if (this.state.error) {
      return (
        <div className="fr-alert fr-alert--error">
          <p>{window.gettext("The selected HDF5 map could not be loaded.")}</p>
        </div>
      );
    }
    return this.props.children;
  }
}

export default function HDF5MapModal({
  modalId,
  entry,
  fetchFn,
  onClose,
}: {
  modalId: string;
  entry: HDF5DatasetEntry | null;
  fetchFn: ToolsFetch;
  onClose: () => void;
}) {
  const t = {
    close: window.gettext("Close"),
    loading: window.gettext("Loading map visualization..."),
  };

  const fetcher = useMemo(() => createToolsH5GroveFetcher(fetchFn), [fetchFn]);

  useEffect(() => {
    if (!entry) {
      return;
    }
    const modalElement = document.getElementById(modalId);
    if (modalElement && window.dsfr) {
      window.dsfr(modalElement).modal.disclose();
    }
  }, [entry, modalId]);

  return (
    <dialog
      aria-labelledby={`${modalId}-title`}
      role="dialog"
      id={modalId}
      className="fr-modal"
    >
      <div
        className="fr-container fr-container--fluid fr-container-md"
        css={modalContainerStyle}
      >
        <div className="fr-modal__body">
          <div className="fr-modal__header">
            <button
              className="fr-btn--close fr-btn"
              aria-controls={modalId}
              type="button"
              onClick={onClose}
            >
              {t.close}
            </button>
          </div>
          <div className="fr-modal__content" css={modalContentStyle}>
            <h1 id={`${modalId}-title`} className="fr-modal__title">
              {entry ? getMapModalTitle(entry) : window.gettext("Map")}
            </h1>
            {entry && (
              <H5GroveProvider
                url="/hdf5"
                filepath={entry.filePath}
                fetcher={fetcher}
                getExportURL={() => undefined}
              >
                <HDF5MapErrorBoundary key={entry.id}>
                  <Suspense fallback={<p>{t.loading}</p>}>
                    <HDF5MapContent entry={entry} />
                  </Suspense>
                </HDF5MapErrorBoundary>
              </H5GroveProvider>
            )}
          </div>
        </div>
      </div>
    </dialog>
  );
}

function HDF5MapContent({ entry }: { entry: HDF5DatasetEntry }) {
  if (entry.dataKind !== "map") {
    throw new Error("Expected selected HDF5 entry to be a map.");
  }

  const dataset = useEntity(entry.datasetPath);
  assertDataset(dataset, "Expected selected HDF5 entry to be a dataset.");
  assertArrayShape(dataset, "Expected selected HDF5 entry to be an array.");
  assertNumericType(dataset, "Expected selected HDF5 entry to be numeric.");

  if (dataset.shape.length !== 3) {
    throw new Error(
      "Expected selected HDF5 map entry to be a three-dimensional array.",
    );
  }

  const { attrValuesStore } = useDataContext();
  const acquisition = useEntity(entry.acquisitionPath || "/");
  const detector = useEntity(entry.groupPath);
  const metadataRows = buildMapMetadataRows(entry, {
    ...use(attrValuesStore.get(acquisition)),
    ...use(attrValuesStore.get(detector)),
    ...use(attrValuesStore.get(dataset)),
  });

  return (
    <div css={visualizationLayoutStyle}>
      <aside css={metadataPanelStyle}>
        <HDF5MetadataPanel rows={metadataRows} />
      </aside>
      <Suspense
        fallback={
          <div css={[mainPanelStyle, visualizationLoadingStyle]}>
            <HDF5DataLoadingIndicator
              datasetPath={entry.datasetPath}
              filePath={entry.filePath}
              label={window.gettext("Loading map visualization...")}
            />
          </div>
        }
      >
        <HDF5MapVisualizationContent
          dataset={dataset}
          entryId={entry.id}
          metadataRows={metadataRows}
        />
      </Suspense>
    </div>
  );
}

function HDF5MapVisualizationContent({
  dataset,
  entryId,
  metadataRows,
}: {
  dataset: ReturnType<typeof useEntity>;
  entryId: string;
  metadataRows: ScientificMetadataRow[];
}) {
  assertDataset(dataset, "Expected selected HDF5 entry to be a dataset.");
  assertArrayShape(dataset, "Expected selected HDF5 entry to be an array.");
  assertNumericType(dataset, "Expected selected HDF5 entry to be numeric.");

  if (dataset.shape.length !== 3) {
    throw new Error(
      "Expected selected HDF5 map entry to be a three-dimensional array.",
    );
  }

  const [rows, columns, channels] = dataset.shape;
  const [draftRangeStart, setDraftRangeStart] = useState(0);
  const [draftRangeEnd, setDraftRangeEnd] = useState(channels);
  const [rangeStart, setRangeStart] = useState(0);
  const [rangeEnd, setRangeEnd] = useState(channels);

  useEffect(() => {
    setDraftRangeStart(0);
    setDraftRangeEnd(channels);
    setRangeStart(0);
    setRangeEnd(channels);
  }, [channels, entryId]);

  const value = useDatasetValue(dataset);
  const numericValue = useToNumArray(value) as ArrayLike<number>;
  const globalSpectrum = useMemo(
    () => computeGlobalSpectrum(numericValue, rows, columns, channels),
    [numericValue, rows, columns, channels],
  );
  const globalSpectrumArray = useNdArray(globalSpectrum, [channels]);

  const rangeValidation = useMemo(
    () => validateChannelRange(draftRangeStart, draftRangeEnd, channels),
    [draftRangeStart, draftRangeEnd, channels],
  );
  const integratedMap = useMemo(
    () =>
      computeIntegratedMap(
        numericValue,
        rows,
        columns,
        channels,
        rangeStart,
        rangeEnd,
      ),
    [numericValue, rows, columns, channels, rangeStart, rangeEnd],
  );
  const integratedMapArray = useNdArray(integratedMap, [rows, columns]);
  const integratedMapDomain = useDomain(integratedMapArray);

  return (
    <div css={mainPanelStyle}>
      <div css={spectrumAreaStyle}>
        <section css={sectionStyle}>
          <HDF5SpectrumPlot
            dataArray={globalSpectrumArray}
            plotCss={plotStyle}
            title={window.gettext("Global spectrum")}
          />
        </section>
        <aside>
          <ChannelRangeControls
            rangeStart={draftRangeStart}
            rangeEnd={draftRangeEnd}
            channels={channels}
            validationMessage={rangeValidation.message}
            onRangeStartChange={setDraftRangeStart}
            onRangeEndChange={setDraftRangeEnd}
            onApply={() => {
              if (!rangeValidation.isValid) {
                return;
              }
              setRangeStart(draftRangeStart);
              setRangeEnd(draftRangeEnd);
            }}
          />
          <div css={helpCardStyle}>
            <p className="fr-m-0">
              {window.gettext(
                "Select a channel range on the global spectrum to update the integrated intensity map.",
              )}
            </p>
          </div>
        </aside>
      </div>
      <section css={mapSectionStyle}>
        <h2 className="fr-h5" css={sectionTitleStyle}>
          {window.interpolate(
            window.gettext("Integrated intensity map (%s - %s)"),
            [rangeStart.toString(), rangeEnd.toString()],
          )}
        </h2>
        <HeatmapVis
          css={mapStyle}
          dataArray={integratedMapArray}
          domain={integratedMapDomain}
          colorMap="Viridis"
          showGrid
          abscissaParams={{ label: window.gettext("X pixel") }}
          ordinateParams={{ label: window.gettext("Y pixel") }}
        />
      </section>
      <MapSummaryFooter
        channels={channels}
        columns={columns}
        metadataRows={metadataRows}
        rows={rows}
      />
    </div>
  );
}

function MapSummaryFooter({
  channels,
  columns,
  metadataRows,
  rows,
}: {
  channels: number;
  columns: number;
  metadataRows: ScientificMetadataRow[];
  rows: number;
}) {
  const metadataByKey = new Map(
    metadataRows.map((row) => [row.key, row.value]),
  );
  const mapSizeX = metadataByKey.get("mapSizeX");
  const mapSizeY = metadataByKey.get("mapSizeY");
  const pixelSizeX = metadataByKey.get("pixelSizeX");
  const pixelSizeY = metadataByKey.get("pixelSizeY");

  return (
    <div css={summaryFooterStyle}>
      <span css={summaryItemStyle}>
        {window.gettext("Map size")} : {rows} × {columns}{" "}
        {window.gettext("pixels")}
      </span>
      {mapSizeX && mapSizeY && (
        <span css={summaryItemStyle}>
          {window.gettext("Physical size")} : {mapSizeX} × {mapSizeY}
        </span>
      )}
      {pixelSizeX && pixelSizeY && (
        <span css={summaryItemStyle}>
          {window.gettext("Pixel")} : {pixelSizeX} × {pixelSizeY}
        </span>
      )}
      <span css={summaryItemStyle}>
        {window.gettext("Channels")} : {channels}
      </span>
    </div>
  );
}

function ChannelRangeControls({
  rangeStart,
  rangeEnd,
  channels,
  validationMessage,
  onRangeStartChange,
  onRangeEndChange,
  onApply,
}: {
  rangeStart: number;
  rangeEnd: number;
  channels: number;
  validationMessage: string | null;
  onRangeStartChange: (value: number) => void;
  onRangeEndChange: (value: number) => void;
  onApply: () => void;
}) {
  function getNumberValue(event: ChangeEvent<HTMLInputElement>): number {
    return event.currentTarget.valueAsNumber;
  }

  return (
    <aside
      className={`fr-input-group ${validationMessage ? "fr-input-group--error" : ""}`}
      css={rangeCardStyle}
    >
      <fieldset css={rangeFieldsetStyle}>
        <legend className="fr-fieldset__legend fr-text--regular">
          {window.gettext("Channel range")}
        </legend>
        <div css={rangeControlsStyle}>
          <div>
            <label className="fr-label" htmlFor="hdf5-map-channel-start">
              {window.gettext("From")}
            </label>
            <input
              className="fr-input"
              id="hdf5-map-channel-start"
              type="number"
              min={0}
              max={channels}
              step={1}
              value={Number.isNaN(rangeStart) ? "" : rangeStart}
              onChange={(event) => onRangeStartChange(getNumberValue(event))}
            />
          </div>
          <div>
            <label className="fr-label" htmlFor="hdf5-map-channel-end">
              {window.gettext("To")}
            </label>
            <input
              className="fr-input"
              id="hdf5-map-channel-end"
              type="number"
              min={0}
              max={channels}
              step={1}
              value={Number.isNaN(rangeEnd) ? "" : rangeEnd}
              onChange={(event) => onRangeEndChange(getNumberValue(event))}
            />
          </div>
        </div>
        <p className="fr-hint-text" css={rangeHintStyle}>
          {window.interpolate(window.gettext("Range width: %s channels"), [
            Number.isFinite(rangeStart) && Number.isFinite(rangeEnd)
              ? Math.max(0, rangeEnd - rangeStart).toString()
              : "-",
          ])}
        </p>
        {validationMessage && (
          <p id="hdf5-map-channel-error" className="fr-error-text">
            {validationMessage}
          </p>
        )}
        <div css={rangeActionRowStyle}>
          <button
            className="fr-btn fr-btn--sm fr-btn--secondary fr-btn--icon-left fr-icon-check-line"
            css={rangeButtonStyle}
            disabled={!!validationMessage}
            onClick={onApply}
            type="button"
          >
            {window.gettext("Apply")}
          </button>
        </div>
      </fieldset>
    </aside>
  );
}

function buildMapMetadataRows(
  entry: HDF5DatasetEntry,
  attributeValues: Record<string, unknown>,
): ScientificMetadataRow[] {
  return [
    {
      key: "file",
      label: window.gettext("File"),
      value: entry.fileName,
    },
    {
      key: "detector",
      label: window.gettext("Detector"),
      value: entry.detectorName || entry.groupName,
    },
    {
      key: "entry",
      label: window.gettext("Entry"),
      value: entry.datasetPath,
    },
    {
      key: "shape",
      label: window.gettext("Shape"),
      value: entry.shape.join(" × "),
    },
    ...buildScientificMetadataRows(attributeValues),
  ];
}

function getMapModalTitle(entry: HDF5DatasetEntry): string {
  return window.interpolate(window.gettext("%s map — %s"), [
    entry.detectorName || entry.groupName,
    entry.fileName,
  ]);
}

function validateChannelRange(
  rangeStart: number,
  rangeEnd: number,
  channels: number,
): { isValid: boolean; message: string | null } {
  if (!Number.isFinite(rangeStart) || !Number.isFinite(rangeEnd)) {
    return {
      isValid: false,
      message: window.gettext("Enter both channel range bounds."),
    };
  }
  if (!Number.isInteger(rangeStart) || !Number.isInteger(rangeEnd)) {
    return {
      isValid: false,
      message: window.gettext("Channel bounds must be whole numbers."),
    };
  }
  if (rangeStart < 0) {
    return {
      isValid: false,
      message: window.gettext("The lower channel must be at least 0."),
    };
  }
  if (rangeEnd > channels) {
    return {
      isValid: false,
      message: window.gettext(
        "The upper channel must not exceed the number of channels.",
      ),
    };
  }
  if (rangeStart >= rangeEnd) {
    return {
      isValid: false,
      message: window.gettext(
        "The lower channel must be smaller than the upper channel.",
      ),
    };
  }
  return { isValid: true, message: null };
}

function computeGlobalSpectrum(
  values: ArrayLike<number>,
  rows: number,
  columns: number,
  channels: number,
): Float64Array {
  const spectrum = new Float64Array(channels);
  for (let row = 0; row < rows; row += 1) {
    for (let column = 0; column < columns; column += 1) {
      const pixelOffset = (row * columns + column) * channels;
      for (let channel = 0; channel < channels; channel += 1) {
        spectrum[channel] += values[pixelOffset + channel];
      }
    }
  }
  return spectrum;
}

function computeIntegratedMap(
  values: ArrayLike<number>,
  rows: number,
  columns: number,
  channels: number,
  rangeStart: number,
  rangeEnd: number,
): Float64Array {
  const map = new Float64Array(rows * columns);
  for (let row = 0; row < rows; row += 1) {
    for (let column = 0; column < columns; column += 1) {
      const pixelOffset = (row * columns + column) * channels;
      let intensity = 0;
      for (let channel = rangeStart; channel < rangeEnd; channel += 1) {
        intensity += values[pixelOffset + channel];
      }
      map[row * columns + column] = intensity;
    }
  }
  return map;
}
