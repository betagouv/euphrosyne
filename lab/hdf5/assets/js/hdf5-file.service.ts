"use strict";

import { FileService } from "../../../assets/js/file-service";

export class HDF5FileService extends FileService {
  constructor(projectSlug: string, runName: string, fetchFn?: typeof fetch) {
    super(
      `/data/${projectSlug}/runs/${runName}/HDF5`,
      `/data/runs/shared_access_signature`,
      fetchFn,
    );
  }
}
