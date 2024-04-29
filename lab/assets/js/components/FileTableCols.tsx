import { EuphrosyneFile } from "../file-service";
import { formatBytes } from "../utils";
import { Col } from "./FileTable";

export const workplaceTableCols: Col<EuphrosyneFile>[] = [
  { label: window.gettext("File"), key: "name" },
  {
    label: window.gettext("Size"),
    key: "size",
    formatter: (value: string) => formatBytes(parseInt(value)),
  },
];
