"use strict";

import { FileService } from "../../../../assets/js/file-service";

export class ProcessedDataFileService extends FileService {
  constructor(projectSlug: string, runName: string, fetchFn?: typeof fetch) {
    super(
      `/data/${projectSlug}/runs/${runName}/processed_data`,
      `/data/runs/shared_access_signature`,
      fetchFn,
    );
  }
}
