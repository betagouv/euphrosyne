import { Suspense, use } from "react";
import {
  assertArrayShape,
  assertDataset,
  assertNumericType,
  useDataContext,
  useEntity,
} from "@witoldw/h5web-app";

import { HDF5DatasetEntry } from "../../hdf5";
import HDF5DataLoadingIndicator from "../HDF5DataLoadingIndicator";
import HDF5MetadataPanel from "../HDF5MetadataPanel";
import { buildSpectrumMetadataRows } from "./metadata";
import { HDF5SpectrumVisualization } from "./HDF5SpectrumVisualization";
import {
  metadataPanelStyle,
  spectrumLoadingStyle,
  spectrumPanelStyle,
  visualizationLayoutStyle,
} from "./styles";

export function HDF5SpectrumContent({ entry }: { entry: HDF5DatasetEntry }) {
  const t = {
    loadingVisualization: window.gettext("Loading visualization..."),
  };

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
  const metadataRows = buildSpectrumMetadataRows(entry, {
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
            <div css={spectrumLoadingStyle}>
              <HDF5DataLoadingIndicator
                datasetPath={entry.datasetPath}
                filePath={entry.filePath}
                label={t.loadingVisualization}
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
