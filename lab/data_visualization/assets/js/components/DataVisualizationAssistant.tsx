import { FormEvent, lazy, Suspense, useEffect, useState } from "react";
import type { EuphrosyneFile } from "../../../../assets/js/file-service";
import type { ToolsFetch } from "../../../../../shared/js/euphrosyne-tools-client";
import {
  createDataVisualization,
  DataVisualizationError,
} from "../data-visualization-service";
import type {
  DataVisualizationErrorCode,
  DataVisualizationResponse,
} from "../types";

const DataVisualizationChart = lazy(() => import("./DataVisualizationChart"));

export default function DataVisualizationAssistant({
  projectSlug,
  files,
  fetchFn,
}: {
  projectSlug: string;
  files: EuphrosyneFile[];
  fetchFn: ToolsFetch;
}) {
  const [selectedPath, setSelectedPath] = useState(files[0]?.path || "");
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<DataVisualizationResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [requestError, setRequestError] = useState<{
    code: DataVisualizationErrorCode | null;
    requestId: string | null;
  } | null>(null);

  useEffect(() => {
    if (!files.some((file) => file.path === selectedPath)) {
      setSelectedPath(files[0]?.path || "");
      setResult(null);
    }
  }, [files, selectedPath]);

  if (files.length === 0) {
    return null;
  }

  const selectedFile = files.find((file) => file.path === selectedPath);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    const normalizedQuestion = question.trim();
    if (!selectedFile || !normalizedQuestion || isLoading) {
      return;
    }
    setIsLoading(true);
    setRequestError(null);
    setResult(null);
    try {
      setResult(
        await createDataVisualization({
          fetchFn,
          projectSlug,
          dataFile: selectedFile,
          question: normalizedQuestion,
        }),
      );
    } catch (error: unknown) {
      const details =
        error instanceof DataVisualizationError
          ? { code: error.code, requestId: error.requestId }
          : { code: null, requestId: null };
      setRequestError(details);
      console.error("Data visualization failed", { ...details, error });
    } finally {
      setIsLoading(false);
    }
  };

  const t = {
    title: window.gettext("Data visualization assistant"),
    scope: window.gettext(
      "Generate a visualization from a TRAUPIXE file in this run.",
    ),
    poweredBy: window.gettext("Powered by Albert"),
    selectedFile: window.gettext("Selected data file:"),
    file: window.gettext("Data file"),
    fileHint: window.gettext(
      "Select the file to use to generate the visualization.",
    ),
    question: window.gettext("Your question"),
    placeholder: window.gettext("Ask a question about the data..."),
    send: window.gettext("Send"),
    loading: window.gettext("Albert is preparing the visualization..."),
    error: window.gettext(
      "The request could not be processed. Please try again.",
    ),
    invalidFilePath: window.gettext("The selected data file path is invalid."),
    unsupportedFileType: window.gettext(
      "The selected data file type is not supported.",
    ),
    fileTooLarge: window.gettext("The selected data file is too large."),
    invalidDataFile: window.gettext("The selected data file is invalid."),
    requestReference: window.gettext("Request reference:"),
    visualization: window.gettext("Visualization"),
    answer: window.gettext("Albert's answer"),
    replacement: window.gettext(
      "Each new question replaces the previous visualization.",
    ),
  };
  const errorMessages: Record<DataVisualizationErrorCode, string> = {
    INVALID_FILE_PATH: t.invalidFilePath,
    UNSUPPORTED_FILE_TYPE: t.unsupportedFileType,
    FILE_TOO_LARGE: t.fileTooLarge,
    INVALID_DATA_FILE: t.invalidDataFile,
  };

  return (
    <section
      className="data-visualization-assistant fr-mt-3w fr-p-2w"
      aria-labelledby="data-visualization-assistant-title"
    >
      <header className="fr-grid-row fr-grid-row--middle fr-mb-1w">
        <h4
          className="fr-mb-0 fr-mr-1w"
          id="data-visualization-assistant-title"
        >
          {t.title}
        </h4>
        <span className="fr-badge fr-badge--sm fr-badge--blue-ecume fr-mr-1w">
          BETA
        </span>
        <span className="fr-hint-text fr-mb-0">{t.poweredBy}</span>
      </header>
      <p className="fr-text--sm fr-mb-2w">{t.scope}</p>

      {files.length === 1 ? (
        <p className="fr-text--sm fr-mb-2w">
          {t.selectedFile} <strong>{files[0].name}</strong>
        </p>
      ) : (
        <div className="fr-grid-row">
          <div className="fr-select-group fr-col-12 fr-col-md-7 fr-mb-3w">
            <label className="fr-label" htmlFor="data-visualization-file">
              {t.file}
              <span className="fr-hint-text">{t.fileHint}</span>
            </label>
            <select
              className="fr-select"
              id="data-visualization-file"
              value={selectedPath}
              disabled={isLoading}
              onChange={(event) => {
                setSelectedPath(event.target.value);
                setResult(null);
                setRequestError(null);
              }}
            >
              {files.map((file) => (
                <option value={file.path} key={file.path}>
                  {file.name}
                </option>
              ))}
            </select>
          </div>
        </div>
      )}

      <form onSubmit={submit}>
        <div className="fr-grid-row fr-grid-row--gutters fr-grid-row--bottom">
          <div className="fr-col-12 fr-col-md-10">
            <div className="fr-input-group">
              <label className="fr-label" htmlFor="data-visualization-question">
                {t.question}
              </label>
              <input
                className="fr-input"
                id="data-visualization-question"
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                placeholder={t.placeholder}
                disabled={isLoading}
              />
            </div>
          </div>
          <div className="fr-col-12 fr-col-md-2">
            <button
              className="fr-btn data-visualization-assistant__submit"
              type="submit"
              disabled={!question.trim() || !selectedFile || isLoading}
            >
              {t.send}
            </button>
          </div>
        </div>
      </form>

      <div aria-live="polite">
        {isLoading && <p className="fr-mt-2w">{t.loading}</p>}
        {requestError && (
          <div className="fr-alert fr-alert--error fr-alert--sm fr-mt-2w">
            <p>
              {requestError.code ? errorMessages[requestError.code] : t.error}
            </p>
            {requestError.requestId && (
              <p className="fr-text--sm">
                <strong>{t.requestReference}</strong> {requestError.requestId}
              </p>
            )}
          </div>
        )}
      </div>

      {result && (
        <>
          <div className="fr-grid-row fr-grid-row--gutters fr-mt-2w">
            <div className="fr-col-12 fr-col-xl-8 fr-col--top">
              <section className="data-visualization-assistant__panel fr-p-2w">
                <h5>{t.visualization}</h5>
                <Suspense fallback={<p>{t.loading}</p>}>
                  <div className="fr-grid-row fr-grid-row--gutters">
                    {result.visualizations.map((visualization, index) => (
                      <div
                        className="fr-col-12"
                        key={`${visualization.title}-${index}`}
                      >
                        <DataVisualizationChart visualization={visualization} />
                      </div>
                    ))}
                  </div>
                </Suspense>
              </section>
            </div>
            <div className="fr-col-12 fr-col-xl-4 fr-col--top">
              <section className="data-visualization-assistant__panel data-visualization-assistant__answer fr-p-2w">
                <h5>{t.answer}</h5>
                <p className="data-visualization-assistant__answer-content">
                  {result.answer}
                </p>
              </section>
            </div>
          </div>
          <p className="fr-hint-text fr-mt-1w">{t.replacement}</p>
        </>
      )}
    </section>
  );
}
