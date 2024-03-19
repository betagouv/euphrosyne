"use strict";

import { FileService } from "../../../../assets/js/file-service.js";

export class ProcessedDataFileService extends FileService {
  constructor(projectSlug: string, runName: string) {
    super(
      `/data/${projectSlug}/runs/${runName}/processed_data`,
      `/data/runs/shared_access_signature`
    );
  }
}
