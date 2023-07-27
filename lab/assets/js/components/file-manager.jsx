import React, { useState, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Fuse from "fuse.js";

import FileUploadForm from "./file-upload-form.jsx";
import FileTable from "./file-table.jsx";

import { displayMessage } from "../utils.js";
export default function FileManager({
  fileService,
  title,
  queryKey,
  enableFormUpload = true,
  formUploadHintText = null,
  cols = ["name", "lastModified", "size"],
}) {
  const [query, setQuery] = useState("");
  const queryClient = useQueryClient();

  // File Table

  const [folder, setFolder] = useState([]);

  const downloadFile = async (file) => {
    const url = await fileService.fetchPresignedURL(file.path);
    window.open(url, "_blank");
  };

  const {
    isLoading,
    data: files,
    refetch,
  } = useQuery(
    [queryKey, fileService.listFileURL, folder],
    async () => {
      const files = await fileService.listData(folder.join("/"));
      return files;
    },
    { refetchOnMount: false, refetchOnReconnect: false }
  );

  const { mutate: deleteFile } = useMutation(
    (file) => fileService.deleteFile(file.path),
    {
      onSuccess: (_data, variable) => {
        queryClient.invalidateQueries([queryKey, fileService.listFileURL]);
        displayMessage(
          window.interpolate(window.gettext("File %s has been removed."), [
            variable.name,
          ]),
          "success"
        );
      },
      onError: (_error, variable) => {
        displayMessage(
          window.interpolate(window.gettext("File %s could not be removed."), [
            variable.name,
          ]),
          "error"
        );
      },
    }
  );

  // File Search

  const fuse = useMemo(() => {
    return new Fuse(files, {
      includeScore: true,
      keys: ["name"],
    });
  }, [files]);

  const filteredFiles = useMemo(() => {
    if (query === "") {
      return files;
    }
    return fuse.search(query).map((i) => i.item);
  }, [fuse, query]);

  const onFileSearch = (e) => {
    setQuery(e.target.value);
  };

  // File Upload

  const onFilesUploaded = () => {
    refetch();
  };

  const onFilesUploadError = () => {
    displayMessage(
      window.interpolate(window.gettext("File %s could not be uploaded."), [
        result.reason.file.name,
      ]) +
        " " +
        result.reason.message,
      "error"
    );
  };

  return (
    <div>
      {enableFormUpload && (
        <FileUploadForm
          hintText={formUploadHintText}
          fileService={fileService}
          onUploadSuccess={onFilesUploaded}
          onUploadError={onFilesUploadError}
        />
      )}
      <div>
        <h3>{title}</h3>
        <div className="fr-grid-row">
          <div className="fr-col-12">
            <FileTable
              cols={cols}
              files={filteredFiles}
              loading={isLoading}
              folder={folder}
              setFolder={setFolder}
              searchQuery={query}
              onFileSearch={onFileSearch}
              onFileDelete={deleteFile}
              onFileDownload={downloadFile}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
