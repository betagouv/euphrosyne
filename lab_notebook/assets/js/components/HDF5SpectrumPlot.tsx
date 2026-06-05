import { css, SerializedStyles } from "@emotion/react";
import { useMemo, useState } from "react";
import {
  LineVis,
  ScaleSelector,
  ScaleType,
  useDomain,
} from "@witoldw/h5web-lib";
import type { AxisScaleType, LineVisProps } from "@witoldw/h5web-lib";

const spectrumHeaderStyle = css({
  alignItems: "center",
  display: "flex",
  flexWrap: "wrap",
  gap: "0.5rem 1rem",
  justifyContent: "space-between",
  marginBottom: "0.5rem",
});

const spectrumTitleStyle = css({
  alignItems: "center",
  display: "flex",
  gap: "0.5rem",
  marginBottom: 0,
});

const spectrumScaleControlStyle = css({
  alignItems: "center",
  display: "flex",
  gap: "0.5rem",
  marginBottom: 0,
  position: "relative",
  zIndex: 2,
  '[role="listbox"]': {
    zIndex: 3000,
  },
});

export default function HDF5SpectrumPlot({
  dataArray,
  plotCss,
  title,
}: {
  dataArray: LineVisProps["dataArray"];
  plotCss: SerializedStyles;
  title: string;
}) {
  const channels = dataArray.shape[0] || 0;
  const [xScaleType, setXScaleType] = useState<
    ScaleType.Linear | ScaleType.Log
  >(ScaleType.Linear);
  const [yScaleType, setYScaleType] = useState<
    ScaleType.Linear | ScaleType.Log
  >(ScaleType.Linear);
  const isXLogScale = xScaleType === ScaleType.Log;
  const ignoreValue = useMemo<LineVisProps["ignoreValue"]>(
    () =>
      yScaleType === ScaleType.Log ? (value: number) => value <= 0 : undefined,
    [yScaleType],
  );
  const domain = useDomain(dataArray, yScaleType, undefined, ignoreValue);
  const abscissas = useMemo(
    () => createChannelAbscissas(channels, isXLogScale),
    [channels, isXLogScale],
  );

  return (
    <>
      <div css={spectrumHeaderStyle}>
        <h2 className="fr-h5" css={spectrumTitleStyle}>
          {title}
        </h2>
        <div css={spectrumScaleControlStyle}>
          <ScaleSelector
            label="X"
            value={xScaleType}
            onScaleChange={setXScaleType}
            options={[ScaleType.Linear, ScaleType.Log]}
          />
          <ScaleSelector
            label="Y"
            value={yScaleType}
            onScaleChange={setYScaleType}
            options={[ScaleType.Linear, ScaleType.Log]}
          />
        </div>
      </div>
      <LineVis
        css={plotCss}
        dataArray={dataArray}
        domain={domain}
        ordinateLabel={window.gettext("Counts")}
        abscissaParams={{
          label: window.gettext("Channel"),
          scaleType: xScaleType as AxisScaleType,
          value: abscissas,
        }}
        ignoreValue={ignoreValue}
        scaleType={yScaleType}
        showGrid
      />
    </>
  );
}

function createChannelAbscissas(
  channels: number,
  useLogScale: boolean,
): Float64Array | undefined {
  if (!useLogScale) {
    return undefined;
  }

  const abscissas = new Float64Array(channels);
  for (let channel = 0; channel < channels; channel += 1) {
    // A logarithmic axis cannot include zero, so log mode displays channels as 1-based positions.
    abscissas[channel] = channel + 1;
  }
  return abscissas;
}
