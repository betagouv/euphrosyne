import { useRef, useState } from "react";
import { displayMessage } from "../../../../assets/js/utils";
import { getFileInputCustomValidity } from "../document-upload-form";

interface DocumentUploadModalProps {
  id: string;
  hintText?: string;
  onUploadFile: (files: File[]) => Promise<
    PromiseSettledResult<{
      file: File;
    }>[]
  >;
  onAnyUploadSucccess: () => void;
  onUploadError: (fileName: string) => void;
}

const validateFileInput = (event: React.FormEvent<HTMLInputElement>) => {
  const fileInput = event.target as HTMLInputElement;
  const { files } = fileInput;
  fileInput.setCustomValidity(
    getFileInputCustomValidity(Array.from(files || []))
  );
};

export default function DocumentUploadModal({
  id,
  hintText,
  onAnyUploadSucccess,
  onUploadFile,
  onUploadError,
}: DocumentUploadModalProps) {
  const t = {
    "An error has occured while generating the presigned URL. Please contact the support team.":
      window.gettext(
        "An error has occured while generating the presigned URL. Please contact the support team."
      ),
    "File %s has been uploaded.": window.gettext("File %s has been uploaded."),
    Close: window.gettext("Close"),
    "Add files": window.gettext("Add files"),
    Upload: window.gettext("Upload"),
    "Add a document": window.gettext("Add a document"),
  };
  const [isSubmitting, setIsSubmitting] = useState(false);
  const formRef = useRef<HTMLFormElement>(null);

  const onSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    uploadFiles();
  };

  const uploadFiles = async () => {
    console.log("uploading...");
    if (!formRef.current) {
      throw new Error("Form ref not set");
    }
    let results;
    setIsSubmitting(true);
    try {
      results = await onUploadFile(Array.from(formRef.current.files.files));
      console.log(results);
    } catch (error) {
      console.log("error uploading...", error);
      displayMessage(
        t[
          "An error has occured while generating the presigned URL. Please contact the support team."
        ],
        "error"
      );
      setIsSubmitting(false);
      throw error;
    }
    results.forEach(async (result) => {
      console.log("result...", result);
      if (result.status === "fulfilled") {
        displayMessage(
          window.interpolate(t["File %s has been uploaded."], [
            result.value.file.name,
          ]),
          "success"
        );
      } else {
        displayMessage(
          window.interpolate(window.gettext("File %s could not be uploaded."), [
            result.reason.file?.name,
          ]) +
            " " +
            result.reason.message,
          "error"
        );
        await onUploadError(result.reason.file?.name || "");
      }
    });
    if (
      results.map((result) => result.status === "fulfilled").indexOf(true) !==
      -1
    ) {
      onAnyUploadSucccess();
    }
    setIsSubmitting(false);
    formRef.current.reset();
  };

  return (
    <dialog
      aria-labelledby={`${id}-title`}
      role="dialog"
      id={id}
      className="fr-modal"
    >
      <div className="fr-container fr-container--fluid fr-container-md">
        <div className="fr-grid-row fr-grid-row--center">
          <div className="fr-col-12 fr-col-md-8 fr-col-lg-6">
            <div className="fr-modal__body">
              <div className="fr-modal__header">
                <button
                  className="fr-btn--close fr-btn"
                  title={t["Close"]}
                  aria-controls={id}
                >
                  {t["Close"]}
                </button>
              </div>
              <div className="fr-modal__content">
                <h1 id={`${id}-title`} className="fr-modal__title">
                  <span className="fr-icon-arrow-right-line fr-icon--lg"></span>
                  {t["Add a document"]}
                </h1>
                <form onSubmit={onSubmit} ref={formRef}>
                  <div className="fr-mb-4w">
                    <div className="fr-upload-group">
                      <label className="fr-label" htmlFor="file-upload">
                        {t["Add files"]}
                        {hintText && (
                          <span className="fr-hint-text">{hintText}</span>
                        )}
                      </label>
                      <input
                        className="fr-upload"
                        type="file"
                        name="files"
                        multiple
                        required
                        onChange={validateFileInput}
                      />
                    </div>
                    <input
                      value={t["Upload"]}
                      className="button fr-mt-2w"
                      type="submit"
                      id="upload-button"
                      disabled={isSubmitting}
                    />
                  </div>
                </form>
              </div>
            </div>
          </div>
        </div>
      </div>
    </dialog>
  );
}
