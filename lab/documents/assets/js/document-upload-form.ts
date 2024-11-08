const ALLOWED_FILE_FORMATS = [
  "7z",
  "csv",
  "dat",
  "db",
  "dbf",
  "doc",
  "docx",
  "jpeg",
  "jpg",
  "heif",
  "log",
  "ods",
  "odt",
  "opd",
  "pdf",
  "png",
  "ppt",
  "pptx",
  "rar",
  "raw",
  "rtf",
  "sql",
  "svg",
  "tar.gz",
  "tiff",
  "txt",
  "wps",
  "wks",
  "wpd",
  "xls",
  "xlsx",
  "xml",
  "zip",
  "par",
  "nra",
  "xnra",
  "geo",
  "str",
  "spc",
  "prf",
  "tcn",
  "il0",
  "g20",
  "g70",
  "r135",
  "r150",
  "x0",
  "x1",
  "x10",
  "x11",
  "x12",
  "x13",
  "x2",
  "x3",
  "x4",
  "x6",
  "par",
  "ini",
  "csv",
  "xlsx",
  "xls",
  "txt",
];

export const getFileInputCustomValidity = (files: File[] | null) => {
  if (!files || files.length === 0) {
    return window.gettext("Please select a file");
  }

  const notSupportedFormats = files
    .map((file) => file.name.split(".").pop()?.toLowerCase())
    .filter((format) => ALLOWED_FILE_FORMATS.indexOf(format || "") === -1);
  if (notSupportedFormats.length > 0) {
    return window.interpolate(
      window.gettext("The following file formats are not accepted : %s"),
      [notSupportedFormats.join(", ")],
    );
  }

  return "";
};
