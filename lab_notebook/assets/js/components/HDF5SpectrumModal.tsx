import { css } from "@emotion/react";
import { Component, ReactNode, Suspense, use, useEffect, useMemo } from "react";

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
  minHeight: "70vh",
});

const visualizationLayoutStyle = css({
  display: "grid",
  gridTemplateColumns: "minmax(15rem, 18rem) minmax(0, 1fr)",
  minHeight: "62vh",
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

const spectrumPanelStyle = css({
  minWidth: 0,
  padding: "1rem 1.25rem",
});

const visualizationLoadingStyle = css({
  alignItems: "center",
  display: "flex",
  minHeight: "28rem",
});

const plotStyle = css({
  minHeight: "28rem",
  height: "62vh",
});

interface HDF5ErrorBoundaryProps {
  children: ReactNode;
}

class HDF5ErrorBoundary extends Component<
  HDF5ErrorBoundaryProps,
  { error: Error | null }
> {
  constructor(props: HDF5ErrorBoundaryProps) {
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
          <p>
            {window.gettext("The selected HDF5 spectrum could not be loaded.")}
          </p>
        </div>
      );
    }
    return this.props.children;
  }
}

export default function HDF5SpectrumModal({
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
    title: window.gettext("Data visualization"),
    close: window.gettext("Close"),
    loading: window.gettext("Loading visualization..."),
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
      <div className="fr-container fr-container--fluid fr-container-md">
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
              {t.title}
            </h1>
            {entry && (
              <H5GroveProvider
                url="/hdf5"
                filepath={entry.filePath}
                fetcher={fetcher}
                getExportURL={() => undefined}
              >
                <HDF5ErrorBoundary key={entry.id}>
                  <Suspense fallback={<p>{t.loading}</p>}>
                    <HDF5SpectrumContent entry={entry} />
                  </Suspense>
                </HDF5ErrorBoundary>
              </H5GroveProvider>
            )}
          </div>
        </div>
      </div>
    </dialog>
  );
}

function HDF5SpectrumContent({ entry }: { entry: HDF5DatasetEntry }) {
  if (entry.dataKind !== "spectrum") {
    throw new Error("Expected selected HDF5 entry to be a spectrum.");
  }

  const dataset = useEntity(entry.datasetPath);
  assertDataset(dataset, "Expected selected HDF5 entry to be a dataset.");
  assertArrayShape(dataset, "Expected selected HDF5 entry to be an array.");
  assertNumericType(dataset, "Expected selected HDF5 entry to be numeric.");

  if (dataset.shape.length !== 1) {
    throw new Error(
      "Expected selected HDF5 entry to be a one-dimensional array.",
    );
  }

  const { attrValuesStore } = useDataContext();
  const group = useEntity(entry.groupPath);
  const metadataRows = buildModalMetadataRows(entry, {
    ...use(attrValuesStore.get(group)),
    ...use(attrValuesStore.get(dataset)),
  });

  return (
    <div css={visualizationLayoutStyle}>
      <aside css={metadataPanelStyle}>
        <HDF5MetadataPanel rows={metadataRows} />
      </aside>
      <section css={spectrumPanelStyle}>
        <Suspense
          fallback={
            <div css={visualizationLoadingStyle}>
              <HDF5DataLoadingIndicator
                datasetPath={entry.datasetPath}
                filePath={entry.filePath}
                label={window.gettext("Loading visualization...")}
              />
            </div>
          }
        >
          <HDF5SpectrumVisualization
            dataset={dataset}
            title={entry.datasetName}
          />
        </Suspense>
      </section>
    </div>
  );
}

function HDF5SpectrumVisualization({
  dataset,
  title,
}: {
  dataset: ReturnType<typeof useEntity>;
  title: string;
}) {
  assertDataset(dataset, "Expected selected HDF5 entry to be a dataset.");
  assertArrayShape(dataset, "Expected selected HDF5 entry to be an array.");
  assertNumericType(dataset, "Expected selected HDF5 entry to be numeric.");

  if (dataset.shape.length !== 1) {
    throw new Error(
      "Expected selected HDF5 entry to be a one-dimensional array.",
    );
  }

  const value = useDatasetValue(dataset);
  const numericValue = useToNumArray(value);
  const dataArray = useNdArray(numericValue, dataset.shape);

  return (
    <HDF5SpectrumPlot dataArray={dataArray} plotCss={plotStyle} title={title} />
  );
}

function buildModalMetadataRows(
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
      key: "entry",
      label: window.gettext("Entry"),
      value: entry.datasetPath,
    },
    {
      key: "group",
      label: window.gettext("Measurement group"),
      value: entry.groupName,
    },
    ...buildScientificMetadataRows(attributeValues),
  ];
}
