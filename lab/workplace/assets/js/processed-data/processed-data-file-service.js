"use strict";

import { FileService } from "../../../../assets/js/file-service.js";

export class ProcessedDataFileService extends FileService {
  constructor(projectName, runName) {
    super(
      `/data/${projectName}/runs/${runName}/processed_data`,
      `/data/${projectName}/runs/${runName}/processed_data/shared_access_signature`
    );
  }
}
