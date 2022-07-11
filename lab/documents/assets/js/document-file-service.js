"use strict";

import { FileService } from "../../../assets/js/file-service.js";

export class DocumentFileService extends FileService {
  constructor(projectName) {
    super(
      `/data/${projectName}/documents`,
      `/data/${projectName}/documents/shared_access_signature`
    );
  }
}
