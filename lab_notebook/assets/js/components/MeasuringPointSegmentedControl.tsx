import { HTMLProps, useId } from "react";

const measuringPointTypes = ["objectGroup", "standard"] as const;
export type MeasuringPointType = (typeof measuringPointTypes)[number];

interface IMeasuringPointSegmentedControlProps {
  selectedType: MeasuringPointType;
  onTypeSelect: (mode: MeasuringPointType) => void;
}

export default function MeasuringPointSegmentedControl({
  selectedType,
  onTypeSelect,
  className,
  disabled,
  ...props
}: IMeasuringPointSegmentedControlProps & HTMLProps<HTMLFieldSetElement>) {
  const _id = useId();
  const t = {
    objectGroup: window.gettext("Object"),
    standard: window.gettext("Standard"),
    legend: window.gettext("Analysis type"),
  };
  return (
    <fieldset className={`fr-segmented ${className}`} {...props}>
      <legend className="fr-segmented__legend">{t.legend}</legend>
      <div className="fr-segmented__elements">
        {measuringPointTypes.map((type) => (
          <div
            className="fr-segmented__element fr-background-default--grey"
            key={`segmented-${_id}-${type}`}
          >
            <input
              value={type}
              checked={selectedType === type}
              type="radio"
              id={`segmented-${_id}-${type}`}
              name={`segmented-${_id}-${type}`}
              onClick={() => {
                onTypeSelect(type);
              }}
              readOnly={true}
              disabled={disabled}
            />
            <label className="fr-label" htmlFor={`segmented-${_id}-${type}`}>
              {t[type]}
            </label>
          </div>
        ))}
      </div>
    </fieldset>
  );
}
