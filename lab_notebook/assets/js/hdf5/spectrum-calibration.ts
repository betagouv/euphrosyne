export interface SpectrumCalibration {
  a: number;
  b: number;
  c: number;
}

export type SpectrumXAxisUnit = "channel" | "energy";

export function parseSpectrumCalibration(
  value: unknown,
): SpectrumCalibration | null {
  if (value === undefined || value === null) {
    return null;
  }

  const text = Array.isArray(value) ? value.join(", ") : String(value);
  const coefficients = new Map<string, number>();
  const coefficientPattern =
    /\b(?:MCA\s*)?([abc])\s*=\s*([-+]?\d*\.?\d+(?:e[-+]?\d+)?)/gi;
  let match: RegExpExecArray | null;

  while ((match = coefficientPattern.exec(text)) !== null) {
    coefficients.set(match[1].toLowerCase(), Number(match[2]));
  }

  const a = coefficients.get("a");
  const b = coefficients.get("b");
  const c = coefficients.get("c");

  if (
    a === undefined ||
    b === undefined ||
    c === undefined ||
    !Number.isFinite(a) ||
    !Number.isFinite(b) ||
    !Number.isFinite(c)
  ) {
    return null;
  }

  return { a, b, c };
}

export function calculateEnergy(
  channel: number,
  calibration: SpectrumCalibration,
) {
  return calibration.a * channel + calibration.b + calibration.c * channel ** 2;
}

export function createEnergyAbscissas(
  channels: number,
  calibration: SpectrumCalibration,
): Float64Array {
  const abscissas = new Float64Array(channels);
  for (let channel = 0; channel < channels; channel += 1) {
    abscissas[channel] = calculateEnergy(channel, calibration);
  }
  return abscissas;
}

export function hasOnlyPositiveValues(values: Float64Array) {
  return values.every((value) => value > 0);
}

export function formatEnergy(value: number) {
  if (!Number.isFinite(value)) {
    return "-";
  }
  return value.toLocaleString(undefined, {
    maximumFractionDigits: 3,
    minimumFractionDigits: Math.abs(value) < 1 ? 2 : 0,
  });
}
