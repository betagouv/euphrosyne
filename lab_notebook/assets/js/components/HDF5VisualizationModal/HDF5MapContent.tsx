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
import { HDF5MapVisualization } from "./HDF5MapVisualization";
import { buildMapMetadataRows } from "./metadata";
import {
  mapPanelStyle,
  metadataPanelStyle,
  visualizationLayoutStyle,
  visualizationLoadingStyle,
} from "./styles";

export function HDF5MapContent({ entry }: { entry: HDF5DatasetEntry }) {
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
          <div css={[mapPanelStyle, visualizationLoadingStyle]}>
            <HDF5DataLoadingIndicator
              datasetPath={entry.datasetPath}
              filePath={entry.filePath}
              label={window.gettext("Loading map visualization...")}
            />
          </div>
        }
      >
        <HDF5MapVisualization
          dataset={dataset}
          entryId={entry.id}
          metadataRows={metadataRows}
        />
      </Suspense>
    </div>
  );
}
