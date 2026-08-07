import { FormEvent, lazy, Suspense, useEffect, useState } from "react";
import type { EuphrosyneFile } from "../../../../lab/assets/js/file-service";
import type { ToolsFetch } from "../../../../shared/js/euphrosyne-tools-client";
import {
  createDataVisualization,
  DataVisualizationError,
} from "../data-visualization/data-visualization-service";
import type { DataVisualizationResponse } from "../data-visualization/types";

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
    requestId: string | null;
    reason: string | null;
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
          ? { requestId: error.requestId, reason: error.reason }
          : { requestId: null, reason: null };
      setRequestError(details);
      console.error("Data visualization failed", { ...details, error });
    } finally {
      setIsLoading(false);
    }
  };

  const t = {
    title: window.gettext("Data visualization assistant"),
    selectedFile: window.gettext("Selected data file:"),
    file: window.gettext("Data file"),
    question: window.gettext("Your question"),
    placeholder: window.gettext("Ask a question about the data..."),
    send: window.gettext("Send"),
    loading: window.gettext("Albert is preparing the visualization..."),
    error: window.gettext(
      "The request could not be processed. Please try again.",
    ),
    reason: window.gettext("Reason:"),
    requestReference: window.gettext("Request reference:"),
    visualization: window.gettext("Visualization"),
    answer: window.gettext("Albert's answer"),
    replacement: window.gettext(
      "Each new question replaces the previous visualization.",
    ),
  };

  return (
    <section
      className="data-visualization-assistant fr-mt-3w"
      aria-labelledby="data-visualization-assistant-title"
    >
      <header className="data-visualization-assistant__header">
        <h4 id="data-visualization-assistant-title">{t.title}</h4>
        <span className="fr-badge fr-badge--sm fr-badge--blue-ecume">BETA</span>
      </header>

      {files.length === 1 ? (
        <p className="fr-text--sm fr-mb-2w">
          {t.selectedFile} <strong>{files[0].name}</strong>
        </p>
      ) : (
        <div className="fr-select-group data-visualization-assistant__file-select">
          <label className="fr-label" htmlFor="data-visualization-file">
            {t.file}
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
      )}

      <form onSubmit={submit}>
        <label className="fr-label" htmlFor="data-visualization-question">
          {t.question}
        </label>
        <div className="data-visualization-assistant__question">
          <input
            className="fr-input"
            id="data-visualization-question"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder={t.placeholder}
            disabled={isLoading}
          />
          <button
            className="fr-btn"
            type="submit"
            disabled={!question.trim() || !selectedFile || isLoading}
          >
            {t.send}
          </button>
        </div>
      </form>

      <div aria-live="polite">
        {isLoading && <p className="fr-mt-2w">{t.loading}</p>}
        {requestError && (
          <div className="fr-alert fr-alert--error fr-alert--sm fr-mt-2w">
            <p>{t.error}</p>
            {requestError.reason && (
              <p className="fr-text--sm">
                <strong>{t.reason}</strong> {requestError.reason}
              </p>
            )}
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
          <div className="data-visualization-assistant__result fr-mt-2w">
            <section>
              <h5>{t.visualization}</h5>
              <Suspense fallback={<p>{t.loading}</p>}>
                <div className="data-visualization-assistant__charts">
                  {result.visualizations.map((visualization, index) => (
                    <DataVisualizationChart
                      key={`${visualization.title}-${index}`}
                      visualization={visualization}
                    />
                  ))}
                </div>
              </Suspense>
            </section>
            <section className="data-visualization-assistant__answer">
              <h5>{t.answer}</h5>
              <p className="data-visualization-assistant__answer-content">
                {result.answer}
              </p>
            </section>
          </div>
          <p className="fr-hint-text fr-mt-1w">{t.replacement}</p>
        </>
      )}
    </section>
  );
}
