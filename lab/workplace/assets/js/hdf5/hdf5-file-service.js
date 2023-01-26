"use strict";

import { FileService } from "../../../../assets/js/file-service.js";

export class HDF5FileService extends FileService {
  constructor(projectSlug, runName) {
    super(
      `/data/${projectSlug}/runs/${runName}/HDF5`,
      `/data/runs/shared_access_signature`
    );
  }
}
