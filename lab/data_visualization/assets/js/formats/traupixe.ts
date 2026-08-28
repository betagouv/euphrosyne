import type { DataVisualizationFormat } from "../types";

const MAX_FILE_SIZE = 100 * 1024 * 1024;

export const TRAUPIXE_FORMAT: DataVisualizationFormat = {
  accepts: (file) => {
    const name = file.name.toLocaleLowerCase();
    return (
      !file.isDir &&
      name.includes("traupixe") &&
      name.endsWith(".xlsx") &&
      file.size !== null &&
      file.size > 0 &&
      file.size <= MAX_FILE_SIZE
    );
  },
};
