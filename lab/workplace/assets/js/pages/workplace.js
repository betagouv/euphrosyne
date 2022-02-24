"use strict";

import "@gouvfr/dsfr/dist/component/component.min.css";
import "@gouvfr/dsfr/dist/component/upload/upload.min.css";
import "@gouvfr/dsfr/dist/component/tab/tab.min.css";

import "@gouvfr/dsfr/dist/component/tab/tab.module.js";

import { FileTable } from "../../../../assets/js/components/file-table.js";
import { FileUploadForm } from "../../../../assets/js/components/file-upload-form.js";
import { initRawData } from "../raw-data/index.js";
import { initProcessedData } from "../processed-data/index.js";

FileTable.init();
FileUploadForm.init();

initRawData();
initProcessedData();
