export interface IStandard {
  label: string;
}

export interface IMeasuringPointStandard {
  id: number;
  standard: IStandard;
}

export type RunMeasuringPointStandards = {
  [measuringPointId: number]: IMeasuringPointStandard;
};
