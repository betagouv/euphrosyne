"use strict";

import { FileService } from "../../../../assets/js/file-service.js";

export class ProcessedDataFileService extends FileService {
  constructor(projectName, runName) {
    super(
      `/data/${projectName}/runs/${runName}/processed_data`,
      `/data/runs/shared_access_signature`
    );
  }
}
