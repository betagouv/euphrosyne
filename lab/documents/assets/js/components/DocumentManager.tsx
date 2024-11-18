import { useState, useEffect } from "react";
import { css } from "@emotion/react";

import { formatBytes } from "../../../../assets/js/utils";
import { EuphrosyneFile } from "../../../../assets/js/file-service";
import { DocumentFileService } from "../document-file-service";

import FileTable, { Col } from "../../../../assets/js/components/FileTable";
import DocumentUploadModal from "./DocumentUploadModal";
import BaseFileActionCell from "../../../../assets/js/components/BaseFileActionCell";
import { IImagewithUrl } from "../../../../../lab_notebook/assets/js/IImageTransform";
import { ProjectImageServices } from "../project-image-service";
import ImageGrid from "../../../../../lab_notebook/assets/js/components/ImageGrid";
import ImageWithPlaceholder from "../../../../../lab_notebook/assets/js/ImageWithPlaceholder";
import { uploadFile } from "../../../../assets/js/blob-service";
import { useClientContext } from "../../../../../shared/js/EuphrosyneToolsClient.context";

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
    formatter: (value: string | null) =>
      value ? new Date(value).toLocaleDateString() : "",
  },
  {
    label: window.gettext("Size"),
    key: "size",
    formatter: (value: string | null) =>
      value ? formatBytes(parseInt(value)) : "",
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
  const t = {
    "Add a document": window.gettext("Add a document"),
    Images: window.gettext("Images"),
  };

  const [isLoading, setIsLoading] = useState(true);
  const [files, setFiles] = useState<EuphrosyneFile[]>([]);

  const [images, setImages] = useState<IImagewithUrl[]>([]);

  const toolsClient = useClientContext();

  const fileService = new DocumentFileService(
    project.name,
    project.slug,
    toolsClient.fetchFn,
  );
  const imageService = new ProjectImageServices(
    project.slug,
    toolsClient.fetchFn,
  );

  const uploadFiles = async (files: File[]) => {
    const images = files.filter((file) => file.type.startsWith("image/"));
    const documents = files.filter((file) => !file.type.startsWith("image/"));
    const documentPromises = fileService.uploadFiles(documents);
    const imagePromises = images.map(async (i) => {
      const url = await imageService.getUploadSASUrl(i.name);
      return uploadFile(i, url);
    });
    return Promise.allSettled([...documentPromises, ...imagePromises]);
  };

  const fetchFiles = async () => {
    setIsLoading(true);
    const promises = [
      fileService.listData().then(setFiles),
      imageService.listProjectImages().then(setImages),
    ];
    await Promise.allSettled(promises);
    setIsLoading(false);
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
        {t["Add a document"]}
      </button>

      <FileTable
        rows={files}
        cols={tableCols}
        isLoading={isLoading}
        actionCell={
          <BaseFileActionCell
            canDelete={table.canDelete}
            onDeleteSuccess={fetchFiles}
            fileService={fileService}
            setIsLoading={setIsLoading}
          />
        }
      />

      <h2>{t["Images"]}</h2>
      <ImageGrid hideFrom={10}>
        {images.map((image) => (
          <ImageWithPlaceholder
            key={image.url.split("?")[0]}
            src={image.url}
            alt=""
          />
        ))}
      </ImageGrid>

      <DocumentUploadModal
        id={uploadModalId}
        onUploadFile={(files: File[]) => uploadFiles(files)}
        onUploadError={(fileName: string) => fileService.deleteFile(fileName)}
        onAnyUploadSucccess={fetchFiles}
        hintText={form.hintText}
      />
    </div>
  );
}
