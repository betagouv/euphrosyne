import { useState, useEffect } from "react";
import { css } from "@emotion/react";

import FileTable, { Col } from "../../../../assets/js/components/FileTable";
import { DocumentFileService } from "../document-file-service";
import { EuphrosyneFile } from "../../../../assets/js/file-service";
import DocumentTableActionCell from "./DocumentTableActionCell";
import { displayMessage, formatBytes } from "../../../../assets/js/utils";
import DocumentUploadModal from "./DocumentUploadModal";

interface DocumentManagerProps {
  project: {
    name: string;
    slug: string;
  };
  table: {
    canDelete: boolean;
  };
  form: {
    hintText: string;
  };
}

const tableCols: Col<EuphrosyneFile>[] = [
  { label: window.gettext("File"), key: "name" },
  {
    label: window.gettext("Last modified"),
    key: "lastModified",
    formatter: (value: string) => new Date(value).toLocaleDateString(),
  },
  {
    label: window.gettext("Size"),
    key: "size",
    formatter: (value: string) => formatBytes(parseInt(value)),
  },
];

const uploadModalId = "upload-document-modal";

const modalBtnStyle = css({
  float: "right",
});

export default function DocumentManager({
  project,
  table,
  form,
}: DocumentManagerProps) {
  const [isLoading, setIsLoading] = useState(true);
  const [files, setFiles] = useState<EuphrosyneFile[]>([]);

  const fileService = new DocumentFileService(project.name, project.slug);

  const fetchFiles = async () => {
    setIsLoading(true);
    const files = await fileService.listData();
    setFiles(files);
    setIsLoading(false);
  };

  const deleteFile = async (name: string, path: string) => {
    if (
      !window.confirm(
        window.interpolate(window.gettext("Delete the document %s ?"), [name])
      )
    ) {
      return;
    }
    setIsLoading(true);
    try {
      await fileService.deleteFile(path);
    } catch (error) {
      displayMessage(
        window.interpolate(window.gettext("File %s could not be removed."), [
          name,
        ]),
        "error"
      );
      setIsLoading(false);
    }
    fetchFiles();
    setIsLoading(false);
    displayMessage(
      window.interpolate(window.gettext("File %s has been removed."), [name]),
      "success"
    );
  };

  const downloadFile = async (path: string) => {
    const url = await fileService.fetchPresignedURL(path);
    window.open(url, "_blank");
  };

  useEffect(() => {
    fetchFiles();
  }, []);

  return (
    <div>
      <button
        type="button"
        className="fr-btn fr-btn--secondary fr-btn--icon-left fr-icon-upload-line fr-mb-3w"
        data-fr-opened="false"
        aria-controls={uploadModalId}
        css={modalBtnStyle}
      >
        {window.gettext("Add a document")}
      </button>

      <FileTable
        rows={files}
        cols={tableCols}
        isLoading={isLoading}
        actionCell={
          <DocumentTableActionCell
            canDelete={table.canDelete}
            onDeleteClick={deleteFile}
            onDownloadClick={downloadFile}
          />
        }
      />

      <DocumentUploadModal
        id={uploadModalId}
        onUploadFile={(files: File[]) => fileService.uploadFiles(files)}
        onUploadError={(fileName: string) => fileService.deleteFile(fileName)}
        onAnyUploadSucccess={fetchFiles}
        hintText={form.hintText}
      />
    </div>
  );
}
