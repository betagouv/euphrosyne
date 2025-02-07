export interface IStandard {
  label: string;
}

export interface IMeasuringPointStandard {
  id: string;
  standard: IStandard;
}

export type RunMeasuringPointStandards = {
  [measuringPointId: string]: IMeasuringPointStandard;
};
