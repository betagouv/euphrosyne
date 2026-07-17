# HDF5 notebook module

This folder contains the notebook-specific HDF5 integration. It converts HDF5
metadata returned by the tools service into entries that can be listed beside
measurement points and visualized in the notebook.

## Files

- `index.ts` is the public import surface for the notebook UI.
- `types.ts` defines the validated HDF5 tree shape and notebook-facing entry
  contracts.
- `hdf5-service.ts` fetches HDF5 metadata/data and reports dataset transfer
  progress for large visualizations.
- `notebook-hdf5.ts` contains notebook-domain logic: HDF5 file filtering,
  measurement-point matching, file summaries, dataset classification, and entry
  creation.
- `notebook-generation/` contains HDF5-to-notebook generation discovery,
  preview, candidate selection, and generation runner code.
- `map-computation.ts` contains map-specific numeric helpers for global spectra,
  integrated maps, and channel range validation.
- `NotebookHDF5.context.ts` provides HDF5 entry loading state and actions to
  notebook components without threading HDF5 props through unrelated component
  layers.
- `scientific-metadata.ts` defines the scientific metadata fields displayed in
  HDF5 visualizations.

## Current behavior

The notebook exposes spectrum and map entries per measurement point.

Spectrum entries are numeric one-dimensional datasets whose names match the
expected spectrum patterns (`X<digits>`, `G<digits>`, or `R<digits>`).

Map entries are numeric three-dimensional datasets named `maps`, with shape
`[y, x, channel]`. Map files are discovered from the `HDF5_maps_files` folder
and associated to measurement points from the point key in the file name.

The inline visualization is shared by both entry kinds:

- spectra render as a line plot;
- maps render a global spectrum, channel range controls, and a 2D integrated
  intensity map for the selected range.

## Import rule

Consumers outside this folder should import from `../hdf5`, not from individual
files. Keep direct file imports inside this folder unless there is a strong
reason to expose a new symbol through `index.ts`.
