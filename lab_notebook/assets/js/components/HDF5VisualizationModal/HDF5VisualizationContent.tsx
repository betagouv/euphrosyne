import { HDF5DatasetEntry } from "../../hdf5";
import { HDF5MapContent } from "./HDF5MapContent";
import { HDF5SpectrumContent } from "./HDF5SpectrumContent";

export function HDF5VisualizationContent({
  entry,
}: {
  entry: HDF5DatasetEntry;
}) {
  if (entry.dataKind === "map") {
    return <HDF5MapContent entry={entry} />;
  }
  return <HDF5SpectrumContent entry={entry} />;
}
