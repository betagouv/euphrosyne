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
