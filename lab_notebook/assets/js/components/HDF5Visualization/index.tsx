import { Suspense, useMemo } from "react";
import { H5GroveProvider } from "@witoldw/h5web-app";

import { createToolsH5GroveFetcher, HDF5DatasetEntry } from "../../hdf5";
import { ToolsFetch } from "../../../../../shared/js/euphrosyne-tools-client";
import { HDF5VisualizationContent } from "./HDF5VisualizationContent";
import { HDF5VisualizationErrorBoundary } from "./HDF5VisualizationErrorBoundary";

export default function HDF5InlineVisualization({
  entry,
  fetchFn,
}: {
  entry: HDF5DatasetEntry;
  fetchFn: ToolsFetch;
}) {
  const t = {
    loadingVisualization: window.gettext("Loading visualization..."),
  };

  const fetcher = useMemo(() => createToolsH5GroveFetcher(fetchFn), [fetchFn]);

  return (
    <H5GroveProvider
      url="/hdf5"
      filepath={entry.filePath}
      fetcher={fetcher}
      getExportURL={() => undefined}
    >
      <HDF5VisualizationErrorBoundary key={entry.id}>
        <Suspense fallback={<p>{t.loadingVisualization}</p>}>
          <HDF5VisualizationContent entry={entry} />
        </Suspense>
      </HDF5VisualizationErrorBoundary>
    </H5GroveProvider>
  );
}
