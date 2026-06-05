# HDF5 notebook module

This folder contains the notebook-specific HDF5 integration. It converts HDF5
metadata returned by the tools service into notebook entries that can be listed
beside measuring points and visualized by React components.

## Files

- `index.ts` is the public import surface for the rest of the notebook UI.
- `types.ts` defines the validated HDF5 tree shape and the notebook-facing entry
  contracts.
- `hdf5-service.ts` fetches HDF5 metadata/data and validates tools-service JSON
  into the locked `HDF5Entity` union.
- `notebook-hdf5.ts` contains notebook-domain logic: HDF5 file filtering,
  measuring-point matching, file summaries, dataset classification, and
  `HDF5DatasetEntry` creation.
- `NotebookHDF5.context.ts` provides HDF5 entry state and actions to notebook
  components without threading HDF5 props through unrelated component layers.
- `scientific-metadata.ts` defines the scientific metadata fields displayed in
  HDF5 visualizations.

## Current behavior

The notebook currently exposes only spectrum entries to users. Spectrum entries
are numeric one-dimensional datasets whose names match the expected spectrum
patterns (`X<digits>`, `G<digits>`, or `R<digits>`).

Map datasets are already represented internally as a future dataset kind:

```ts
export type HDF5DatasetEntryKind = "spectrum" | "map";
```

`notebook-hdf5.ts` classifies numeric two-dimensional non-image datasets as
maps, but `SUPPORTED_DATASET_ENTRY_KINDS` currently contains only `"spectrum"`.
This keeps the UI behavior unchanged until a map viewer exists.

## Adding map support

When a map visualization is ready:

1. Add `"map"` to `SUPPORTED_DATASET_ENTRY_KINDS` in `notebook-hdf5.ts`.
2. Route map entries to a map-specific modal/component instead of
   `HDF5SpectrumModal`.
3. Keep spectrum-specific validation in `HDF5SpectrumModal`; map validation
   should live in the map viewer.
4. Add tests that assert map entries are created with `dataKind: "map"`,
   `dataKindLabel: "Map"`, and the expected metadata summary.

## Import rule

Consumers outside this folder should import from `../hdf5`, not from individual
files. Keep direct file imports inside this folder unless there is a strong
reason to expose a new symbol through `index.ts`.
