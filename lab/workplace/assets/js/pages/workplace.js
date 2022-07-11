"use strict";

import "@gouvfr/dsfr/dist/component/tab/tab.module.js";

import { FileTable } from "../../../../assets/js/components/file-table.js";
import { FileUploadForm } from "../../../../assets/js/components/file-upload-form.js";
import { initRawData } from "../raw-data/index.js";
import { initProcessedData } from "../processed-data/index.js";
import { VirtualOfficeButton } from "../components/virtual-office-button.js";
FileTable.init();
FileUploadForm.init();
VirtualOfficeButton.init();

initRawData();
initProcessedData();
