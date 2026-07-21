"use strict";

import { FileService } from "../../../assets/js/file-service";
import { ToolsFetch } from "../../../../shared/js/euphrosyne-tools-client";

export class HDF5FileService extends FileService {
  constructor(projectSlug: string, runName: string, fetchFn?: ToolsFetch) {
    super(
      `/data/${projectSlug}/runs/${runName}/HDF5`,
      `/data/runs/shared_access_signature`,
      fetchFn,
    );
  }
}
