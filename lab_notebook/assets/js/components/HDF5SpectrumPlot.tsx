import { css, SerializedStyles } from "@emotion/react";
import { useMemo, useState } from "react";
import {
  LineVis,
  ScaleSelector,
  ScaleType,
  useDomain,
} from "@witoldw/h5web-lib";
import type { AxisScaleType, LineVisProps } from "@witoldw/h5web-lib";
import {
  createEnergyAbscissas,
  hasOnlyPositiveValues,
  type SpectrumCalibration,
  type SpectrumXAxisUnit,
} from "../hdf5";

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
  flexWrap: "wrap",
  gap: "0.5rem",
  marginBottom: 0,
  position: "relative",
  zIndex: 2,
  '[role="listbox"]': {
    zIndex: 3000,
  },
});

const spectrumUnitControlStyle = css({
  alignItems: "center",
  display: "flex",
  position: "relative",
  ".hdf5-spectrum-unit-label": {
    alignSelf: "center",
    color: "var(--h5w-toolbar-label--color, royalblue)",
    margin: "0 0.25rem",
    whiteSpace: "nowrap",
  },
});

const spectrumUnitButtonStyle = css({
  alignItems: "center",
  background: "transparent",
  border: 0,
  color: "inherit",
  cursor: "pointer",
  display: "flex",
  font: "inherit",
  padding: "0 0.25rem",
  ".hdf5-spectrum-unit-button-like": {
    alignItems: "center",
    borderRadius: "0.5rem",
    display: "flex",
    height: "var(--h5w-btn--height, 1.875rem)",
    justifyContent: "center",
    padding: "0 0.5rem",
    transition:
      "background-color 0.05s ease-in-out, box-shadow 0.05s ease-in-out",
    whiteSpace: "nowrap",
  },
  "&:hover .hdf5-spectrum-unit-button-like": {
    backgroundColor: "var(--h5w-btn-hover--bgColor, whitesmoke)",
    boxShadow:
      "-1px -1px 2px inset var(--h5w-btn-hover--shadowColor, var(--h5w-btnRaised--shadowColor, gray))",
  },
  '&[aria-expanded="true"] .hdf5-spectrum-unit-button-like': {
    backgroundColor: "var(--h5w-btnPressed--bgColor, white)",
    boxShadow:
      "1px 1px 2px inset var(--h5w-btnPressed--shadowColor, var(--h5w-btnRaised--shadowColor, gray))",
  },
  ".hdf5-spectrum-unit-arrow": {
    borderLeft: "0.25rem solid transparent",
    borderRight: "0.25rem solid transparent",
    borderTop: "0.3rem solid var(--h5w-selector-arrowIcon--color, dimgray)",
    height: 0,
    marginLeft: "0.5rem",
    width: 0,
  },
});

const spectrumUnitMenuStyle = css({
  backgroundColor: "var(--h5w-selector-menu--bgColor, white)",
  boxShadow: "#0000001a 0 0 0 1px, #0000001a 0 4px 11px",
  display: "flex",
  flexDirection: "column",
  left: "0.25rem",
  minWidth: "calc(100% - 0.5rem)",
  padding: "0.25rem 0",
  position: "absolute",
  top: "calc(100% + 0.25rem)",
  zIndex: 3000,
});

const spectrumUnitOptionStyle = css({
  alignItems: "center",
  background: "transparent",
  border: 0,
  color: "inherit",
  cursor: "pointer",
  display: "flex",
  font: "inherit",
  padding: "0.5rem 0.75rem",
  textAlign: "left",
  whiteSpace: "nowrap",
  "&:hover, &[aria-selected='true']": {
    backgroundColor: "var(--h5w-selector-option-hover--bgColor, whitesmoke)",
  },
});

export default function HDF5SpectrumPlot({
  calibration = null,
  dataArray,
  onXAxisUnitChange,
  plotCss,
  title,
  xAxisUnit,
}: {
  calibration?: SpectrumCalibration | null;
  dataArray: LineVisProps["dataArray"];
  onXAxisUnitChange?: (unit: SpectrumXAxisUnit) => void;
  plotCss: SerializedStyles;
  title: string;
  xAxisUnit?: SpectrumXAxisUnit;
}) {
  const t = {
    channel: window.gettext("Channel"),
    channels: window.gettext("Channels"),
    energy: window.gettext("Energy"),
    energyKeV: window.gettext("Energy (keV)"),
    counts: window.gettext("Counts"),
    xUnit: window.gettext("X unit"),
  };
  const channels = dataArray.shape[0] || 0;
  const [internalXAxisUnit, setInternalXAxisUnit] =
    useState<SpectrumXAxisUnit>("channel");
  const [isXAxisUnitMenuOpen, setIsXAxisUnitMenuOpen] = useState(false);
  const [xScaleType, setXScaleType] = useState<
    ScaleType.Linear | ScaleType.Log
  >(ScaleType.Linear);
  const [yScaleType, setYScaleType] = useState<
    ScaleType.Linear | ScaleType.Log
  >(ScaleType.Linear);
  const ignoreValue = useMemo<LineVisProps["ignoreValue"]>(
    () =>
      yScaleType === ScaleType.Log ? (value: number) => value <= 0 : undefined,
    [yScaleType],
  );
  const domain = useDomain(dataArray, yScaleType, undefined, ignoreValue);
  const selectedXAxisUnit = xAxisUnit || internalXAxisUnit;
  const canUseEnergyAxis = Boolean(calibration);
  const effectiveXAxisUnit =
    selectedXAxisUnit === "energy" && canUseEnergyAxis ? "energy" : "channel";
  const energyAbscissas = useMemo(
    () => (calibration ? createEnergyAbscissas(channels, calibration) : null),
    [calibration, channels],
  );
  const canUseEnergyLogScale =
    !energyAbscissas || hasOnlyPositiveValues(energyAbscissas);
  const availableXScaleOptions =
    effectiveXAxisUnit === "energy" && !canUseEnergyLogScale
      ? [ScaleType.Linear]
      : [ScaleType.Linear, ScaleType.Log];
  const effectiveXScaleType =
    effectiveXAxisUnit === "energy" &&
    !canUseEnergyLogScale &&
    xScaleType === ScaleType.Log
      ? ScaleType.Linear
      : xScaleType;
  const isXLogScale = effectiveXScaleType === ScaleType.Log;
  const abscissas = useMemo(
    () =>
      effectiveXAxisUnit === "energy" && energyAbscissas
        ? energyAbscissas
        : createChannelAbscissas(channels, isXLogScale),
    [channels, effectiveXAxisUnit, energyAbscissas, isXLogScale],
  );
  const selectedXAxisUnitLabel =
    effectiveXAxisUnit === "energy" ? t.energy : t.channels;
  const xAxisUnitOptions: { label: string; value: SpectrumXAxisUnit }[] = [
    { label: t.channels, value: "channel" },
    { label: t.energy, value: "energy" },
  ];
  const handleXAxisUnitChange = (unit: SpectrumXAxisUnit) => {
    setInternalXAxisUnit(unit);
    onXAxisUnitChange?.(unit);
    setIsXAxisUnitMenuOpen(false);
  };
  const handleXScaleChange = (scaleType: ScaleType) => {
    if (scaleType === ScaleType.Linear || scaleType === ScaleType.Log) {
      setXScaleType(scaleType);
    }
  };
  const handleYScaleChange = (scaleType: ScaleType) => {
    if (scaleType === ScaleType.Linear || scaleType === ScaleType.Log) {
      setYScaleType(scaleType);
    }
  };

  return (
    <>
      <div css={spectrumHeaderStyle}>
        <h2 className="fr-h5" css={spectrumTitleStyle}>
          {title}
        </h2>
        <div css={spectrumScaleControlStyle}>
          {calibration && (
            <div css={spectrumUnitControlStyle}>
              <span className="hdf5-spectrum-unit-label">{t.xUnit}</span>
              <button
                aria-expanded={isXAxisUnitMenuOpen}
                aria-haspopup="listbox"
                css={spectrumUnitButtonStyle}
                onClick={() => setIsXAxisUnitMenuOpen((isOpen) => !isOpen)}
                type="button"
              >
                <span className="hdf5-spectrum-unit-button-like">
                  {selectedXAxisUnitLabel}
                  <span className="hdf5-spectrum-unit-arrow" aria-hidden />
                </span>
              </button>
              {isXAxisUnitMenuOpen && (
                <div css={spectrumUnitMenuStyle} role="listbox">
                  {xAxisUnitOptions.map((option) => (
                    <button
                      aria-selected={effectiveXAxisUnit === option.value}
                      css={spectrumUnitOptionStyle}
                      key={option.value}
                      onClick={() => handleXAxisUnitChange(option.value)}
                      role="option"
                      type="button"
                    >
                      {option.label}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
          <ScaleSelector
            label="X"
            value={effectiveXScaleType}
            onScaleChange={handleXScaleChange}
            options={availableXScaleOptions}
          />
          <ScaleSelector
            label="Y"
            value={yScaleType}
            onScaleChange={handleYScaleChange}
            options={[ScaleType.Linear, ScaleType.Log]}
          />
        </div>
      </div>
      <LineVis
        css={plotCss}
        dataArray={dataArray}
        domain={domain}
        ordinateLabel={t.counts}
        abscissaParams={{
          label: effectiveXAxisUnit === "energy" ? t.energyKeV : t.channel,
          scaleType: effectiveXScaleType as AxisScaleType,
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
