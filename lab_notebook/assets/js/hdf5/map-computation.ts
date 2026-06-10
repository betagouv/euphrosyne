export interface ChannelRangeValidation {
  isValid: boolean;
  message: string | null;
}

export function validateChannelRange(
  rangeStart: number,
  rangeEnd: number,
  channels: number,
): ChannelRangeValidation {
  if (!Number.isFinite(rangeStart) || !Number.isFinite(rangeEnd)) {
    return {
      isValid: false,
      message: window.gettext("Enter both channel range bounds."),
    };
  }
  if (!Number.isInteger(rangeStart) || !Number.isInteger(rangeEnd)) {
    return {
      isValid: false,
      message: window.gettext("Channel bounds must be whole numbers."),
    };
  }
  if (rangeStart < 0) {
    return {
      isValid: false,
      message: window.gettext("The lower channel must be at least 0."),
    };
  }
  if (rangeEnd > channels) {
    return {
      isValid: false,
      message: window.gettext(
        "The upper channel must not exceed the number of channels.",
      ),
    };
  }
  if (rangeStart >= rangeEnd) {
    return {
      isValid: false,
      message: window.gettext(
        "The lower channel must be smaller than the upper channel.",
      ),
    };
  }
  return { isValid: true, message: null };
}

export function computeGlobalSpectrum(
  values: ArrayLike<number>,
  rows: number,
  columns: number,
  channels: number,
): Float64Array {
  const spectrum = new Float64Array(channels);
  for (let row = 0; row < rows; row += 1) {
    for (let column = 0; column < columns; column += 1) {
      const pixelOffset = (row * columns + column) * channels;
      for (let channel = 0; channel < channels; channel += 1) {
        spectrum[channel] += values[pixelOffset + channel];
      }
    }
  }
  return spectrum;
}

export function computeIntegratedMap(
  values: ArrayLike<number>,
  rows: number,
  columns: number,
  channels: number,
  rangeStart: number,
  rangeEnd: number,
): Float64Array {
  const map = new Float64Array(rows * columns);
  for (let row = 0; row < rows; row += 1) {
    for (let column = 0; column < columns; column += 1) {
      const pixelOffset = (row * columns + column) * channels;
      let intensity = 0;
      for (let channel = rangeStart; channel < rangeEnd; channel += 1) {
        intensity += values[pixelOffset + channel];
      }
      map[row * columns + column] = intensity;
    }
  }
  return map;
}
