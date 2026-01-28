import { useState } from "react";
import { BlobStorageClient } from "../../../../lab/assets/js/blob-storage-client";
import { ObjectGroupImageServices } from "../notebook-image.services";

const blobStorageClient = new BlobStorageClient();

interface IUploadObjectImageProps {
  onUpload: (url: string) => void;
  service: ObjectGroupImageServices;
}

export default function UploadObjectImage({
  onUpload,
  service,
}: IUploadObjectImageProps) {
  const t = {
    notAnImageError: "Uploaded file must be a valid image.",
    sasUrlError: "An error occurred while requesting upload URL.",
    blobUploadError: "An error occurred while uploading the file.",
    uploadImage: "Upload an image",
    supportedExtensions: "Allowed extensions: png, jpg, jpeg, webp.",
  };
  const [error, setError] = useState<string | null>();
  const [isUploading, setIsUploading] = useState<boolean>(false);

  const handleError = (error: unknown, defaultErrorMessage: string) => {
    setIsUploading(false);
    setError(error instanceof Error ? error.message : defaultErrorMessage);
  };

  const onFileUploadSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files) {
      const file = files[0];

      if (!file.type.startsWith("image/")) {
        setError(t.notAnImageError);
        return;
      }

      if (error) {
        setError(null);
      }

      setIsUploading(true);

      // First get SAS URL from euphro tools
      let url: string;

      try {
        url = await service.getUploadSASUrl(file.name);
      } catch (error) {
        handleError(error, window.gettext(t.sasUrlError));
        throw error;
      }

      // Then, upload to S3-like service
      try {
        await blobStorageClient.upload(file, url);
      } catch (error) {
        handleError(error, t.blobUploadError);
        throw error;
      }

      setIsUploading(false);

      // Reset input value
      e.target.value = "";

      onUpload(url);
    }
  };

  return (
    <div
      className={`fr-upload-group  fr-mt-4w ${error ? "fr-input-group--error" : ""}`}
    >
      <label className="fr-label" htmlFor="add-image-to-object-file-upload">
        <h4>{t.uploadImage}</h4>
        <span className="fr-hint-text">{t.supportedExtensions}</span>
      </label>
      <input
        className="fr-upload"
        type="file"
        id="add-image-to-object-file-upload"
        aria-describedby="add-image-to-object-file-upload-desc-error"
        name="file-upload"
        onChange={onFileUploadSelect}
        disabled={isUploading}
      />
      {error && (
        <p
          id="add-image-to-object-file-upload-desc-error"
          className="fr-error-text"
        >
          {error}
        </p>
      )}
    </div>
  );
}
