"use strict";

import { FileService } from "../../../../assets/js/file-service.js";

export class ProcessedDataFileService extends FileService {
  constructor(projectSlug, runName) {
    super(
      `/data/${projectSlug}/runs/${runName}/processed_data/folders`,
      `/data/runs/shared_access_signature`
    );
  }
}
