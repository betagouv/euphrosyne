import { ChangeEvent } from "react";

import {
  rangeActionRowStyle,
  rangeButtonStyle,
  rangeCardStyle,
  rangeControlsStyle,
  rangeFieldsetStyle,
  rangeHintStyle,
} from "./styles";

export function ChannelRangeControls({
  rangeStart,
  rangeEnd,
  channels,
  validationMessage,
  onRangeStartChange,
  onRangeEndChange,
  onApply,
}: {
  rangeStart: number;
  rangeEnd: number;
  channels: number;
  validationMessage: string | null;
  onRangeStartChange: (value: number) => void;
  onRangeEndChange: (value: number) => void;
  onApply: () => void;
}) {
  function getNumberValue(event: ChangeEvent<HTMLInputElement>): number {
    return event.currentTarget.valueAsNumber;
  }

  return (
    <aside
      className={`fr-input-group ${validationMessage ? "fr-input-group--error" : ""}`}
      css={rangeCardStyle}
    >
      <fieldset css={rangeFieldsetStyle}>
        <legend className="fr-fieldset__legend fr-text--regular">
          {window.gettext("Channel range")}
        </legend>
        <div css={rangeControlsStyle}>
          <div>
            <label className="fr-label" htmlFor="hdf5-map-channel-start">
              {window.gettext("From")}
            </label>
            <input
              className="fr-input"
              id="hdf5-map-channel-start"
              type="number"
              min={0}
              max={channels}
              step={1}
              value={Number.isNaN(rangeStart) ? "" : rangeStart}
              onChange={(event) => onRangeStartChange(getNumberValue(event))}
            />
          </div>
          <div>
            <label className="fr-label" htmlFor="hdf5-map-channel-end">
              {window.gettext("To")}
            </label>
            <input
              className="fr-input"
              id="hdf5-map-channel-end"
              type="number"
              min={0}
              max={channels}
              step={1}
              value={Number.isNaN(rangeEnd) ? "" : rangeEnd}
              onChange={(event) => onRangeEndChange(getNumberValue(event))}
            />
          </div>
        </div>
        <p className="fr-hint-text" css={rangeHintStyle}>
          {window.interpolate(window.gettext("Range width: %s channels"), [
            Number.isFinite(rangeStart) && Number.isFinite(rangeEnd)
              ? Math.max(0, rangeEnd - rangeStart).toString()
              : "-",
          ])}
        </p>
        {validationMessage && (
          <p id="hdf5-map-channel-error" className="fr-error-text">
            {validationMessage}
          </p>
        )}
        <div css={rangeActionRowStyle}>
          <button
            className="fr-btn fr-btn--sm fr-btn--secondary fr-btn--icon-left fr-icon-check-line"
            css={rangeButtonStyle}
            disabled={!!validationMessage}
            onClick={onApply}
            type="button"
          >
            {window.gettext("Apply")}
          </button>
        </div>
      </fieldset>
    </aside>
  );
}
