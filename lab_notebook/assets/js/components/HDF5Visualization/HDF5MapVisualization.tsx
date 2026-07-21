import { useEffect, useMemo, useState } from "react";
import { HeatmapVis, useDomain } from "@witoldw/h5web-lib";
import {
  assertArrayShape,
  assertDataset,
  assertNumericType,
  useDatasetValue,
  useEntity,
  useNdArray,
  useToNumArray,
} from "@witoldw/h5web-app";

import {
  computeGlobalSpectrum,
  computeIntegratedMap,
  ScientificMetadataRow,
  validateChannelRange,
} from "../../hdf5";
import HDF5SpectrumPlot from "../HDF5SpectrumPlot";
import { ChannelRangeControls } from "./ChannelRangeControls";
import { MapSummaryFooter } from "./MapSummaryFooter";
import {
  globalSpectrumPlotStyle,
  helpCardStyle,
  mapPanelStyle,
  mapSectionStyle,
  mapStyle,
  sectionStyle,
  sectionTitleStyle,
  spectrumAreaStyle,
} from "./styles";

export function HDF5MapVisualization({
  dataset,
  entryId,
  metadataRows,
}: {
  dataset: ReturnType<typeof useEntity>;
  entryId: string;
  metadataRows: ScientificMetadataRow[];
}) {
  const t = {
    globalSpectrum: window.gettext("Global spectrum"),
    rangeHelp: window.gettext(
      "Select a channel range on the global spectrum to update the integrated intensity map.",
    ),
    integratedIntensityMap: window.gettext(
      "Integrated intensity map (%s - %s)",
    ),
    xPixel: window.gettext("X pixel"),
    yPixel: window.gettext("Y pixel"),
  };

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
    <div css={mapPanelStyle}>
      <div css={spectrumAreaStyle}>
        <section css={sectionStyle}>
          <HDF5SpectrumPlot
            dataArray={globalSpectrumArray}
            plotCss={globalSpectrumPlotStyle}
            title={t.globalSpectrum}
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
            <p className="fr-m-0">{t.rangeHelp}</p>
          </div>
        </aside>
      </div>
      <section css={mapSectionStyle}>
        <h2 className="fr-h5" css={sectionTitleStyle}>
          {window.interpolate(t.integratedIntensityMap, [
            rangeStart.toString(),
            rangeEnd.toString(),
          ])}
        </h2>
        <HeatmapVis
          css={mapStyle}
          dataArray={integratedMapArray}
          domain={integratedMapDomain}
          colorMap="Viridis"
          showGrid
          abscissaParams={{ label: t.xPixel }}
          ordinateParams={{ label: t.yPixel }}
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
