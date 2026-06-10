import {
  assertArrayShape,
  assertDataset,
  assertNumericType,
  useDatasetValue,
  useEntity,
  useNdArray,
  useToNumArray,
} from "@witoldw/h5web-app";

import HDF5SpectrumPlot from "../HDF5SpectrumPlot";
import { spectrumPlotStyle } from "./styles";

export function HDF5SpectrumVisualization({
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
    <HDF5SpectrumPlot
      dataArray={dataArray}
      plotCss={spectrumPlotStyle}
      title={title}
    />
  );
}
