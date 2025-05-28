import { HTMLProps, useId } from "react";

interface ISgementedSelectModeProps {
  selectedMode: SelectionMode;
  onModeSelect: (mode: SelectionMode) => void;
}

const selectionModes = ["point", "area"] as const;
export type SelectionMode = (typeof selectionModes)[number];

export default function SegmentedSelectMode({
  selectedMode,
  onModeSelect,
  className,
  ...props
}: ISgementedSelectModeProps & HTMLProps<HTMLFieldSetElement>) {
  const t = {
    point: window.gettext("Point"),
    area: window.gettext("Area"),
    legend: window.gettext("Selection mode"),
  };
  const _id = useId();

  const modeDisplay = {
    point: {
      iconClass: "fr-icon-cursor-line",
    },
    area: {
      iconClass: "fr-icon-layout-grid-line",
    },
  };
  return (
    <fieldset
      className={`fr-segmented fr-segmented--no-legend ${className}`}
      {...props}
    >
      <legend className="fr-segmented__legend">{t.legend}</legend>
      <div className="fr-segmented__elements">
        {selectionModes.map((mode) => (
          <div
            className="fr-segmented__element fr-background-default--grey"
            key={`segmented-${mode}`}
          >
            <input
              checked={selectedMode === mode}
              type="radio"
              id={`segmented-${_id}-${mode}`}
              onClick={() => {
                onModeSelect(mode);
              }}
              readOnly={true}
            />
            <label
              className={`fr-label ${modeDisplay[mode].iconClass}`}
              htmlFor={`segmented-${_id}-${mode}`}
            >
              {t[mode]}
            </label>
          </div>
        ))}
      </div>
    </fieldset>
  );
}
